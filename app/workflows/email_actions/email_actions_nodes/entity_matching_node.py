"""Entity matching node for resolving names to database entities"""
from typing import Dict, List, Optional, Any
import logging

from core.nodes.base import Node
from core.task import TaskContext
from database.session import db_session
from services.entity_matching import EntityMatchingService, EntityType, MatchContext
from schemas.email_actions_schema import EmailActionsEventSchema


logger = logging.getLogger(__name__)


class EntityMatchingNode(Node):
    """Resolves entity names to database IDs using the entity matching service"""
    
    def process(self, task_context: TaskContext) -> TaskContext:
        """Process entity matching for extracted entities"""
        
        event: EmailActionsEventSchema = task_context.event
        
        # Get extraction data from previous nodes
        action_type = task_context.nodes.get("IntentClassificationNode", {}).get("action_type", "unknown")
        
        # Get the appropriate extraction node data based on action type
        extraction_data = None
        entities_to_match = []
        
        if action_type == "add_note":
            extraction_data = task_context.nodes.get("AddNoteExtractionNode", {})
            note_params = extraction_data.get("note_parameters", {})
            
            # Get all mentioned entities
            mentioned_entities = note_params.get("mentioned_entities", [])
            primary_entity = note_params.get("primary_entity_name")
            
            # Build list of entities to match
            entities_to_match = mentioned_entities.copy()
            
            # Add primary entity if not already in list
            if primary_entity and not any(e.get("name") == primary_entity for e in mentioned_entities):
                entities_to_match.append({
                    "name": primary_entity,
                    "type": note_params.get("primary_entity_type", "contact")
                })
        
        elif action_type == "log_call":
            extraction_data = task_context.nodes.get("LogCallExtractionNode", {})
            call_params = extraction_data.get("call_log_parameters", {})
            
            # Get participants
            participants = call_params.get("participants", [])
            for participant in participants:
                if isinstance(participant, dict):
                    entities_to_match.append({
                        "name": participant.get("name", ""),
                        "type": "contact"
                    })
                elif isinstance(participant, str):
                    entities_to_match.append({
                        "name": participant,
                        "type": "contact"
                    })
        
        elif action_type == "set_reminder":
            extraction_data = task_context.nodes.get("SetReminderExtractionNode", {})
            reminder_params = extraction_data.get("reminder_parameters", {})
            
            # Get all mentioned entities
            mentioned_entities = reminder_params.get("mentioned_entities", [])
            entities_to_match = mentioned_entities.copy()
            
            # If no entities extracted, try to create from assignee/related entity
            if not entities_to_match:
                assignee = reminder_params.get("assignee")
                if assignee:
                    entities_to_match.append({
                        "name": assignee,
                        "type": "contact"
                    })
                
                related_entity = reminder_params.get("related_entity_name")
                if related_entity and related_entity != assignee:
                    entities_to_match.append({
                        "name": related_entity,
                        "type": "contact"
                    })
        
        # Perform entity matching
        matching_results = self._match_entities(entities_to_match, event)
        
        # Analyze results
        all_matched = all(result["matched"] for result in matching_results["entities"])
        none_matched = not any(result["matched"] for result in matching_results["entities"])
        
        if all_matched:
            match_status = "all_matched"
        elif none_matched:
            match_status = "none_matched"
        else:
            match_status = "partial_matched"
        
        # Update task context
        task_context.update_node(
            node_name=self.node_name,
            entity_matching_complete=True,
            matching_results=matching_results,
            match_status=match_status,
            entities_to_match=entities_to_match
        )
        
        logger.info(f"Entity matching completed: {match_status} - {len(entities_to_match)} entities processed")
        
        return task_context
    
    def _match_entities(self, entities: List[Dict[str, str]], event: EmailActionsEventSchema) -> Dict[str, Any]:
        """
        Match entities using the entity matching service
        
        Args:
            entities: List of entities to match [{"name": "Dr. Smith", "type": "contact"}, ...]
            event: The email event for context
            
        Returns:
            Dictionary with matching results
        """
        results = {
            "entities": [],
            "matched_count": 0,
            "unmatched_count": 0
        }
        
        # Initialize entity matching service
        for session in db_session():
            service = EntityMatchingService(session)
            
            for entity in entities:
                entity_name = entity.get("name", "").strip()
                entity_type = entity.get("type", "contact")
                
                if not entity_name:
                    continue
                
                # Build context from email
                context = self._build_match_context(event)
                
                # Perform matching based on entity type
                matches = []
                if entity_type == "contact":
                    matches = service.match_contact(entity_name, context=context)
                # Add other entity types as needed
                # elif entity_type == "account":
                #     matches = service.match_account(entity_name, context=context)
                
                # Process matches
                if matches:
                    # Take the best match
                    best_match = matches[0]
                    
                    result = {
                        "name": entity_name,
                        "type": entity_type,
                        "matched": True,
                        "match_id": best_match.entity_id,
                        "match_display_name": best_match.display_name,
                        "confidence": best_match.confidence_score,
                        "match_details": {
                            "match_type": best_match.match_type.value,
                            "email": getattr(best_match, "email", None),
                            "organization": getattr(best_match, "organization", None),
                        },
                        "alternatives": [
                            {
                                "id": m.entity_id,
                                "name": m.display_name,
                                "confidence": m.confidence_score
                            } for m in matches[1:3]  # Include up to 2 alternatives
                        ]
                    }
                    results["matched_count"] += 1
                else:
                    result = {
                        "name": entity_name,
                        "type": entity_type,
                        "matched": False,
                        "reason": "No matches found",
                        "suggestions": []
                    }
                    results["unmatched_count"] += 1
                
                results["entities"].append(result)
            
            service.close()
            break
        
        return results
    
    def _build_match_context(self, event: EmailActionsEventSchema) -> Optional[MatchContext]:
        """Build matching context from email event"""
        # Extract organization hints from email domain
        from_domain = event.from_email.split('@')[-1] if '@' in event.from_email else None
        
        # Build context dictionary
        context_dict = {}
        
        # Add organization hint based on email domain
        if from_domain:
            # Map common domains to organizations
            domain_org_map = {
                "cshs.org": "Cedars-Sinai",
                "cedars-sinai.edu": "Cedars-Sinai",
                "ucla.edu": "UCLA",
                "uclahealth.org": "UCLA Health",
                # Add more mappings as needed
            }
            
            if from_domain in domain_org_map:
                context_dict["organization"] = domain_org_map[from_domain]
        
        return MatchContext(**context_dict) if context_dict else None