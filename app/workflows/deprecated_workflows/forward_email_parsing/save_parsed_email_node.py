from datetime import datetime
from typing import Dict, Any
import logging

from core.nodes.base import Node
from core.task import TaskContext
from database.session import db_session
from database.data_models.email_parsed_data import EmailParsed
from workflows.forward_email_parsing.email_parsing_model_config import EmailParsingModelConfig


logger = logging.getLogger(__name__)


class SaveParsedEmailNode(Node):
    """Saves all parsed data to the emails_parsed table"""
    
    def process(self, task_context: TaskContext) -> TaskContext:
        """Consolidate all extracted data and save to database"""
        
        event = task_context.event
        
        # Gather data from all nodes
        type_detection = task_context.nodes.get("EmailTypeDetectionNode", {})
        forwarded_extraction = task_context.nodes.get("ForwardedEmailExtractionNode", {})
        direct_extraction = task_context.nodes.get("DirectEmailExtractionNode", {})
        entity_extraction = task_context.nodes.get("EntityExtractionNode", {})
        meeting_extraction = task_context.nodes.get("MeetingDetailsExtractionNode", {})
        action_extraction = task_context.nodes.get("ActionItemExtractionNode", {})
        entity_resolution = task_context.nodes.get("EntityResolutionNode", {})
        
        # Determine email type and extract relevant data
        email_type = type_detection.get("email_type", "unknown")
        is_forwarded = type_detection.get("is_forwarded", False)
        
        # Get the actual model being used
        provider, model_name = EmailParsingModelConfig.get_model('default')
        model_used = f"{provider.value}:{model_name}"
        
        # Build the parsed email record
        parsed_data = {
            "email_id": event.email_id,
            "parsed_at": datetime.utcnow(),
            "parser_version": "v1.0",
            "model_used": model_used,
            
            # Classification
            "is_forwarded": is_forwarded,
            "is_action_required": forwarded_extraction.get("request_intents", []) != [] or 
                                direct_extraction.get("has_action_required", False),
            "email_type": email_type,
            
            # User request (for forwarded emails)
            "user_request": forwarded_extraction.get("user_request"),
            "request_intents": forwarded_extraction.get("request_intents", []),
            
            # Forwarded metadata
            "forwarded_from": forwarded_extraction.get("forwarded_from"),
            "forwarded_thread_id": forwarded_extraction.get("original_thread_id"),
            
            # Extracted entities
            "people": entity_extraction.get("people", []),
            "organizations": entity_extraction.get("organizations", []),
            "dates_mentioned": entity_extraction.get("dates", []),
            "locations": entity_extraction.get("locations", []),
            
            # Structured content
            "meeting_info": meeting_extraction.get("meeting_info"),
            "action_items": action_extraction.get("action_items", []),
            "key_topics": self._extract_key_topics(task_context),
            
            # Thread context (simplified for now)
            "thread_participants": self._get_unique_participants(entity_extraction),
            "thread_message_count": 1,  # Would need thread analysis
            
            # Analysis
            "sentiment": "neutral",  # Could add sentiment analysis
            "urgency_score": self._calculate_urgency(action_extraction),
            
            # Entity mappings
            "entity_mappings": entity_resolution.get("entity_mappings", {})
        }
        
        # Save to database
        try:
            for session in db_session():
                # Check if already parsed
                existing = session.query(EmailParsed).filter_by(
                    email_id=event.email_id
                ).first()
                
                if existing and not event.force_reparse:
                    logger.info(f"Email {event.email_id} already parsed, skipping")
                    task_context.update_node(
                        node_name=self.node_name,
                        status="already_parsed",
                        parsed_email_id=str(existing.id)
                    )
                else:
                    if existing:
                        # Update existing record
                        for key, value in parsed_data.items():
                            setattr(existing, key, value)
                        parsed_email = existing
                    else:
                        # Create new record
                        parsed_email = EmailParsed(**parsed_data)
                        session.add(parsed_email)
                    
                    session.commit()
                    
                    logger.info(f"Successfully saved parsed email {event.email_id}")
                    task_context.update_node(
                        node_name=self.node_name,
                        status="saved",
                        parsed_email_id=str(parsed_email.id)
                    )
                
                break
                
        except Exception as e:
            logger.error(f"Error saving parsed email: {e}")
            task_context.update_node(
                node_name=self.node_name,
                status="error",
                error=str(e)
            )
        
        return task_context
    
    def _extract_key_topics(self, task_context: TaskContext) -> list:
        """Extract key topics from various nodes"""
        topics = []
        
        # From meeting extraction
        meeting_data = task_context.nodes.get("MeetingDetailsExtractionNode", {})
        if meeting_data.get("topics"):
            topics.extend(meeting_data["topics"])
        
        # From direct email extraction
        direct_data = task_context.nodes.get("DirectEmailExtractionNode", {})
        if direct_data.get("key_topics"):
            topics.extend(direct_data["key_topics"])
        
        # Deduplicate
        return list(set(topics))
    
    def _get_unique_participants(self, entity_data: Dict[str, Any]) -> list:
        """Get unique email participants"""
        participants = []
        people = entity_data.get("people", [])
        
        for person in people:
            if person.get("email"):
                participants.append({
                    "name": person.get("name"),
                    "email": person.get("email")
                })
        
        return participants
    
    def _calculate_urgency(self, action_data: Dict[str, Any]) -> int:
        """Calculate urgency score based on action items"""
        action_items = action_data.get("action_items", [])
        
        if not action_items:
            return 2
        
        # Check for high priority items
        high_priority_count = sum(1 for item in action_items if item.get("priority") == "high")
        
        if high_priority_count > 0:
            return min(7 + high_priority_count, 10)
        elif len(action_items) > 3:
            return 6
        elif len(action_items) > 0:
            return 4
        else:
            return 2