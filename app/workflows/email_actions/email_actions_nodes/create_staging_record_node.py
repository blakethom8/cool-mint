from datetime import datetime, timedelta
from uuid import uuid4
import logging

from core.nodes.base import Node
from core.task import TaskContext
from database.session import db_session
from database.data_models.email_actions import (
    EmailAction, CallLogStaging, NoteStaging, ReminderStaging
)
from schemas.email_actions_schema import EmailActionsEventSchema


logger = logging.getLogger(__name__)


class CreateStagingRecordNode(Node):
    """Creates staging records based on the extracted action data"""
    
    def process(self, task_context: TaskContext) -> TaskContext:
        """Create appropriate staging record based on action type"""
        
        event: EmailActionsEventSchema = task_context.event
        
        # Get classification and extraction data
        classification = task_context.nodes.get("IntentClassificationNode", {})
        action_type = classification.get("action_type", "unknown")
        
        if action_type == "unknown":
            # Skip staging for unknown actions
            task_context.update_node(
                node_name=self.node_name,
                status="skipped",
                reason="Unknown action type"
            )
            return task_context
        
        try:
            for session in db_session():
                # Create EmailAction record first
                email_action = EmailAction(
                    email_id=event.email_id,
                    action_type=action_type,
                    action_parameters=classification.get("initial_parameters", {}),
                    confidence_score=classification.get("confidence_score", 0.0),
                    reasoning=classification.get("reasoning", ""),
                    status="pending"
                )
                session.add(email_action)
                session.flush()  # Get the ID
                
                # Create appropriate staging record
                staging_id = None
                
                if action_type == "log_call":
                    staging_id = self._create_call_log_staging(
                        session, email_action.id, task_context
                    )
                elif action_type == "add_note":
                    staging_id = self._create_note_staging(
                        session, email_action.id, task_context
                    )
                elif action_type == "set_reminder":
                    staging_id = self._create_reminder_staging(
                        session, email_action.id, task_context
                    )
                
                # Commit everything
                session.commit()
                
                task_context.update_node(
                    node_name=self.node_name,
                    status="created",
                    email_action_id=str(email_action.id),
                    staging_record_id=str(staging_id) if staging_id else None,
                    action_type=action_type
                )
                
                logger.info(f"Created staging record for {action_type}: {staging_id}")
                break
                
        except Exception as e:
            logger.error(f"Error creating staging record: {e}")
            task_context.update_node(
                node_name=self.node_name,
                status="error",
                error=str(e)
            )
        
        return task_context
    
    def _create_call_log_staging(self, session, email_action_id, task_context):
        """Create call log staging record with entity matching for participants"""
        
        # Get extracted parameters
        extraction_node = task_context.nodes.get("LogCallExtractionNode", {})
        params = extraction_node.get("call_log_parameters", {})
        
        # Get entity matching results
        matching_node = task_context.nodes.get("EntityMatchingNode", {})
        matching_results = matching_node.get("matching_results", {})
        match_status = matching_node.get("match_status", "none_matched")
        
        # Build lists for matched and unmatched participants
        matched_participants = []
        unmatched_participants = []
        contact_ids = []  # For backward compatibility
        contact_names = []  # For backward compatibility
        
        for entity_result in matching_results.get("entities", []):
            if entity_result.get("matched") and entity_result.get("type") == "contact":
                # Add to matched participants with full details
                matched_participants.append({
                    "id": entity_result.get("match_id"),
                    "name": entity_result.get("match_display_name"),
                    "original_name": entity_result.get("name"),
                    "type": entity_result.get("type"),
                    "confidence": entity_result.get("confidence"),
                    "match_details": entity_result.get("match_details", {})
                })
                # Also add to legacy fields
                contact_ids.append(entity_result.get("match_id"))
                contact_names.append(entity_result.get("match_display_name"))
            else:
                # Add to unmatched participants
                unmatched_participants.append({
                    "name": entity_result.get("name"),
                    "type": entity_result.get("type"),
                    "reason": entity_result.get("reason")
                })
                # Keep unmatched names for user resolution
                contact_names.append(entity_result.get("name"))
        
        # If no entity matching was done, fall back to participant names
        if not matching_results:
            contact_names = [p.get("name") if isinstance(p, dict) else p 
                           for p in params.get("participants", [])]
        
        # Parse activity date if provided
        activity_date = None
        if params.get("activity_date"):
            try:
                activity_date = datetime.fromisoformat(params["activity_date"])
            except:
                activity_date = datetime.now()
        else:
            activity_date = datetime.now()
        
        # Determine primary contact ID
        primary_contact_id = contact_ids[0] if contact_ids else None
        
        # Create staging record with entity matching results
        staging = CallLogStaging(
            email_action_id=email_action_id,
            subject=params.get("subject", "Call/Meeting"),
            description=params.get("description", ""),
            activity_date=activity_date,
            duration_minutes=params.get("duration_minutes"),
            mno_type=params.get("mno_type", "BD_Outreach"),
            mno_subtype=params.get("mno_subtype", "General_Meeting"),
            mno_setting=params.get("mno_setting", "In-Person"),
            contact_ids=contact_names,  # Keep for backward compatibility
            primary_contact_id=primary_contact_id,
            
            # Entity matching fields
            matched_participant_ids=matched_participants,
            unmatched_participants=unmatched_participants,
            entity_match_status=match_status,
            
            suggested_values=params,
            approval_status="pending"
        )
        
        # TODO: Set created_by field when we have user context
        # staging.created_by = current_user_id
        
        session.add(staging)
        session.flush()
        return staging.id
    
    def _create_note_staging(self, session, email_action_id, task_context):
        """Create single note staging record with entity matching results"""
        
        # Get extracted parameters
        extraction_node = task_context.nodes.get("AddNoteExtractionNode", {})
        params = extraction_node.get("note_parameters", {})
        
        # Get entity matching results
        matching_node = task_context.nodes.get("EntityMatchingNode", {})
        matching_results = matching_node.get("matching_results", {})
        match_status = matching_node.get("match_status", "none_matched")
        
        # Collect matched and unmatched entities
        matched_entities = []
        unmatched_entities = []
        primary_entity = None
        
        for entity_result in matching_results.get("entities", []):
            if entity_result.get("matched"):
                entity_data = {
                    "id": entity_result.get("match_id"),
                    "name": entity_result.get("match_display_name"),
                    "original_name": entity_result.get("name"),
                    "type": entity_result.get("type"),
                    "confidence": entity_result.get("confidence"),
                    "match_details": entity_result.get("match_details", {})
                }
                matched_entities.append(entity_data)
                
                # Set primary entity (first matched or explicitly marked primary)
                if not primary_entity or entity_result.get("name") == params.get("primary_entity_name"):
                    primary_entity = entity_data
            else:
                unmatched_entities.append({
                    "name": entity_result.get("name"),
                    "type": entity_result.get("type"),
                    "reason": entity_result.get("reason")
                })
        
        # Determine primary entity for the single record
        if primary_entity:
            # Use the matched primary entity
            related_entity_id = primary_entity["id"]
            related_entity_name = primary_entity["name"]
            related_entity_type = primary_entity["type"]
        else:
            # No matches, use extracted primary entity info
            related_entity_id = None
            related_entity_name = params.get("primary_entity_name")
            related_entity_type = params.get("primary_entity_type", "contact")
        
        # Create single staging record with all entities in JSONB
        staging = NoteStaging(
            email_action_id=email_action_id,
            note_content=params.get("note_content", ""),
            note_type=params.get("note_type", "general"),
            
            # LLM fields
            llm_topics=params.get("topics", []),
            llm_sentiment=params.get("sentiment", "Neutral"),
            
            # Primary entity fields (for backward compatibility)
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
            related_entity_name=related_entity_name,
            
            # All entities in JSONB (matching call log pattern)
            matched_entity_ids=matched_entities,
            unmatched_entities=unmatched_entities,
            entity_match_status=match_status,
            
            # Other fields
            suggested_values=params,
            approval_status="pending"
        )
        
        # TODO: Set created_by field when we have user context
        # staging.created_by = current_user_id
        
        session.add(staging)
        session.flush()
        
        logger.info(f"Created 1 note staging record with {len(matched_entities)} matched entities")
        
        return staging.id
    
    def _create_reminder_staging(self, session, email_action_id, task_context):
        """Create reminder staging record with entity matching results"""
        
        # Get extracted parameters
        extraction_node = task_context.nodes.get("SetReminderExtractionNode", {})
        params = extraction_node.get("reminder_parameters", {})
        
        # Get entity matching results
        matching_node = task_context.nodes.get("EntityMatchingNode", {})
        matching_results = matching_node.get("matching_results", {})
        match_status = matching_node.get("match_status", "none_matched")
        
        # Parse due date
        due_date = datetime.now() + timedelta(days=7)  # Default to 1 week
        if params.get("due_date"):
            try:
                due_date = datetime.fromisoformat(params["due_date"])
            except:
                # Try to parse as a string description
                pass
        
        # Collect matched and unmatched entities
        matched_entities = []
        unmatched_entities = []
        assignee_id = None
        related_entity_id = None
        
        for entity_result in matching_results.get("entities", []):
            if entity_result.get("matched"):
                matched_entities.append({
                    "id": entity_result.get("match_id"),
                    "name": entity_result.get("match_display_name"),
                    "original_name": entity_result.get("name"),
                    "type": entity_result.get("type"),
                    "confidence": entity_result.get("confidence"),
                    "match_details": entity_result.get("match_details", {})
                })
                
                # Set assignee_id if this is the assignee
                if entity_result.get("name") == params.get("assignee"):
                    assignee_id = entity_result.get("match_id")
                
                # Set related_entity_id if this is the related entity
                if entity_result.get("name") == params.get("related_entity_name"):
                    related_entity_id = entity_result.get("match_id")
            else:
                unmatched_entities.append({
                    "name": entity_result.get("name"),
                    "type": entity_result.get("type"),
                    "reason": entity_result.get("reason")
                })
        
        # Create staging record
        staging = ReminderStaging(
            email_action_id=email_action_id,
            reminder_text=params.get("reminder_text", ""),
            due_date=due_date,
            priority=params.get("priority", "normal"),
            assignee=params.get("assignee"),
            assignee_id=assignee_id,  # Matched entity ID
            related_entity_name=params.get("related_entity_name"),
            related_entity_id=related_entity_id,  # Matched entity ID
            related_entity_type="contact",  # Default to contact
            
            # LLM fields
            llm_reminder_category=params.get("reminder_type", "follow_up"),
            
            # Entity matching results
            matched_entity_ids=matched_entities,
            unmatched_entities=unmatched_entities,
            entity_match_status=match_status,
            
            suggested_values=params,
            approval_status="pending"
        )
        
        # TODO: Set created_by field when we have user context
        # staging.created_by = current_user_id
        
        session.add(staging)
        session.flush()
        return staging.id