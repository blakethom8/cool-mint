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
        """Create call log staging record"""
        
        # Get extracted parameters
        extraction_node = task_context.nodes.get("LogCallExtractionNode", {})
        params = extraction_node.get("call_log_parameters", {})
        
        # Parse activity date if provided
        activity_date = None
        if params.get("activity_date"):
            try:
                activity_date = datetime.fromisoformat(params["activity_date"])
            except:
                activity_date = datetime.now()
        else:
            activity_date = datetime.now()
        
        # Create staging record
        staging = CallLogStaging(
            email_action_id=email_action_id,
            subject=params.get("subject", "Call/Meeting"),
            description=params.get("description", ""),
            activity_date=activity_date,
            duration_minutes=params.get("duration_minutes"),
            mno_type=params.get("mno_type", "BD_Outreach"),
            mno_subtype=params.get("mno_subtype", "General_Meeting"),
            mno_setting=params.get("mno_setting", "In-Person"),
            contact_ids=[p.get("name") for p in params.get("participants", [])],
            suggested_values=params,
            approval_status="pending"
        )
        
        session.add(staging)
        session.flush()
        return staging.id
    
    def _create_note_staging(self, session, email_action_id, task_context):
        """Create note staging record"""
        
        # Get extracted parameters
        extraction_node = task_context.nodes.get("AddNoteExtractionNode", {})
        params = extraction_node.get("note_parameters", {})
        
        # Create staging record
        staging = NoteStaging(
            email_action_id=email_action_id,
            note_content=params.get("note_content", ""),
            note_type=params.get("note_type", "general"),
            related_entity_type=params.get("related_entity_type", "contact"),
            related_entity_name=params.get("related_entity_name"),
            suggested_values=params,
            approval_status="pending"
        )
        
        session.add(staging)
        session.flush()
        return staging.id
    
    def _create_reminder_staging(self, session, email_action_id, task_context):
        """Create reminder staging record"""
        
        # Get extracted parameters
        extraction_node = task_context.nodes.get("SetReminderExtractionNode", {})
        params = extraction_node.get("reminder_parameters", {})
        
        # Parse due date
        due_date = datetime.now() + timedelta(days=7)  # Default to 1 week
        if params.get("due_date"):
            try:
                due_date = datetime.fromisoformat(params["due_date"])
            except:
                # Try to parse as a string description
                pass
        
        # Create staging record
        staging = ReminderStaging(
            email_action_id=email_action_id,
            reminder_text=params.get("reminder_text", ""),
            due_date=due_date,
            priority=params.get("priority", "normal"),
            assignee=params.get("assignee"),
            related_entity_name=params.get("related_entity_name"),
            suggested_values=params,
            approval_status="pending"
        )
        
        session.add(staging)
        session.flush()
        return staging.id