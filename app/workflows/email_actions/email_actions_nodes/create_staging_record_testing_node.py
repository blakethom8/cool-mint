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


class CreateStagingRecordTestingNode(Node):
    """Testing version of CreateStagingRecordNode that doesn't commit to database"""
    
    def process(self, task_context: TaskContext) -> TaskContext:
        """Create appropriate staging record based on action type (without committing)"""
        
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
            # Simulate database operations without committing
            simulated_results = {}
            
            # Create mock EmailAction record
            mock_email_action_id = str(uuid4())
            simulated_results["email_action"] = {
                "id": mock_email_action_id,
                "email_id": event.email_id,
                "action_type": action_type,
                "action_parameters": classification.get("initial_parameters", {}),
                "confidence_score": classification.get("confidence_score", 0.0),
                "reasoning": classification.get("reasoning", ""),
                "status": "pending"
            }
            
            # Create appropriate staging record (mock)
            staging_data = None
            
            if action_type == "log_call":
                staging_data = self._create_call_log_staging_mock(
                    mock_email_action_id, task_context
                )
                simulated_results["staging_type"] = "call_log"
            elif action_type == "add_note":
                staging_data = self._create_note_staging_mock(
                    mock_email_action_id, task_context
                )
                simulated_results["staging_type"] = "note"
            elif action_type == "set_reminder":
                staging_data = self._create_reminder_staging_mock(
                    mock_email_action_id, task_context
                )
                simulated_results["staging_type"] = "reminder"
            
            simulated_results["staging_records"] = staging_data
            
            # Log what would have been created
            logger.info(f"[TESTING MODE] Would create {action_type} staging record(s)")
            logger.info(f"[TESTING MODE] Mock email_action_id: {mock_email_action_id}")
            if isinstance(staging_data, list):
                logger.info(f"[TESTING MODE] Would create {len(staging_data)} staging records")
            
            task_context.update_node(
                node_name=self.node_name,
                status="simulated",
                email_action_id=mock_email_action_id,
                staging_data=staging_data,
                action_type=action_type,
                simulated_results=simulated_results,
                test_mode=True
            )
            
        except Exception as e:
            logger.error(f"Error in testing staging record: {e}")
            task_context.update_node(
                node_name=self.node_name,
                status="error",
                error=str(e),
                test_mode=True
            )
        
        return task_context
    
    def _create_call_log_staging_mock(self, email_action_id, task_context):
        """Mock call log staging record creation with entity matching"""
        
        extraction_node = task_context.nodes.get("LogCallExtractionNode", {})
        params = extraction_node.get("call_log_parameters", {})
        
        matching_node = task_context.nodes.get("EntityMatchingNode", {})
        matching_results = matching_node.get("matching_results", {})
        match_status = matching_node.get("match_status", "none_matched")
        
        matched_participants = []
        unmatched_participants = []
        contact_ids = []
        contact_names = []
        
        for entity_result in matching_results.get("entities", []):
            if entity_result.get("matched") and entity_result.get("type") == "contact":
                matched_participants.append({
                    "id": entity_result.get("match_id"),
                    "name": entity_result.get("match_display_name"),
                    "original_name": entity_result.get("name"),
                    "type": entity_result.get("type"),
                    "confidence": entity_result.get("confidence"),
                    "match_details": entity_result.get("match_details", {})
                })
                contact_ids.append(entity_result.get("match_id"))
                contact_names.append(entity_result.get("match_display_name"))
            else:
                unmatched_participants.append({
                    "name": entity_result.get("name"),
                    "type": entity_result.get("type"),
                    "reason": entity_result.get("reason")
                })
                contact_names.append(entity_result.get("name"))
        
        if not matching_results:
            contact_names = [p.get("name") if isinstance(p, dict) else p 
                           for p in params.get("participants", [])]
        
        activity_date = datetime.now()
        if params.get("activity_date"):
            try:
                activity_date = datetime.fromisoformat(params["activity_date"])
            except:
                pass
        
        primary_contact_id = contact_ids[0] if contact_ids else None
        
        return {
            "id": str(uuid4()),
            "email_action_id": email_action_id,
            "subject": params.get("subject", "Call/Meeting"),
            "description": params.get("description", ""),
            "activity_date": activity_date.isoformat(),
            "duration_minutes": params.get("duration_minutes"),
            "mno_type": params.get("mno_type", "BD_Outreach"),
            "mno_subtype": params.get("mno_subtype", "General_Meeting"),
            "mno_setting": params.get("mno_setting", "In-Person"),
            "contact_ids": contact_names,
            "primary_contact_id": primary_contact_id,
            "matched_participant_ids": matched_participants,
            "unmatched_participants": unmatched_participants,
            "entity_match_status": match_status,
            "suggested_values": params,
            "approval_status": "pending"
        }
    
    def _create_note_staging_mock(self, email_action_id, task_context):
        """Mock note staging record creation (single record with all entities)"""
        
        extraction_node = task_context.nodes.get("AddNoteExtractionNode", {})
        params = extraction_node.get("note_parameters", {})
        
        matching_node = task_context.nodes.get("EntityMatchingNode", {})
        matching_results = matching_node.get("matching_results", {})
        match_status = matching_node.get("match_status", "none_matched")
        
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
            related_entity_id = primary_entity["id"]
            related_entity_name = primary_entity["name"]
            related_entity_type = primary_entity["type"]
        else:
            related_entity_id = None
            related_entity_name = params.get("primary_entity_name")
            related_entity_type = params.get("primary_entity_type", "contact")
        
        # Create single staging record with all entities
        staging_record = {
            "id": str(uuid4()),
            "email_action_id": email_action_id,
            "note_content": params.get("note_content", ""),
            "note_type": params.get("note_type", "general"),
            "llm_topics": params.get("topics", []),
            "llm_sentiment": params.get("sentiment", "Neutral"),
            "related_entity_type": related_entity_type,
            "related_entity_id": related_entity_id,
            "related_entity_name": related_entity_name,
            "matched_entity_ids": matched_entities,
            "unmatched_entities": unmatched_entities,
            "entity_match_status": match_status,
            "suggested_values": params,
            "approval_status": "pending"
        }
        
        logger.info(f"[TESTING MODE] Would create 1 note staging record with {len(matched_entities)} matched entities")
        
        return staging_record
    
    def _create_reminder_staging_mock(self, email_action_id, task_context):
        """Mock reminder staging record creation with entity matching"""
        
        extraction_node = task_context.nodes.get("SetReminderExtractionNode", {})
        params = extraction_node.get("reminder_parameters", {})
        
        matching_node = task_context.nodes.get("EntityMatchingNode", {})
        matching_results = matching_node.get("matching_results", {})
        match_status = matching_node.get("match_status", "none_matched")
        
        due_date = datetime.now() + timedelta(days=7)
        if params.get("due_date"):
            try:
                due_date = datetime.fromisoformat(params["due_date"])
            except:
                pass
        
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
                
                if entity_result.get("name") == params.get("assignee"):
                    assignee_id = entity_result.get("match_id")
                
                if entity_result.get("name") == params.get("related_entity_name"):
                    related_entity_id = entity_result.get("match_id")
            else:
                unmatched_entities.append({
                    "name": entity_result.get("name"),
                    "type": entity_result.get("type"),
                    "reason": entity_result.get("reason")
                })
        
        return {
            "id": str(uuid4()),
            "email_action_id": email_action_id,
            "reminder_text": params.get("reminder_text", ""),
            "due_date": due_date.isoformat(),
            "priority": params.get("priority", "normal"),
            "assignee": params.get("assignee"),
            "assignee_id": assignee_id,
            "related_entity_name": params.get("related_entity_name"),
            "related_entity_id": related_entity_id,
            "related_entity_type": "contact",
            "llm_reminder_category": params.get("reminder_type", "follow_up"),
            "matched_entity_ids": matched_entities,
            "unmatched_entities": unmatched_entities,
            "entity_match_status": match_status,
            "suggested_values": params,
            "approval_status": "pending"
        }