from typing import Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

from core.nodes.agent import AgentNode, AgentConfig
from core.task import TaskContext
from workflows.email_actions.email_actions_model_config import EmailActionsModelConfig
from schemas.email_actions_schema import EmailActionsEventSchema, ReminderParameters


class SetReminderExtractionNode(AgentNode):
    """Extracts information for setting a reminder or follow-up task"""
    
    def get_agent_config(self) -> AgentConfig:
        provider, model = EmailActionsModelConfig.get_model('extraction')
        
        return AgentConfig(
            system_prompt="""You are extracting information to create a reminder or follow-up task.

Extract the following:
1. **Reminder Text**: What needs to be done or remembered
2. **Due Date**: When the reminder should trigger
   - Parse relative dates (e.g., "in 60 days", "next week")
   - Use today's date as reference for calculations
3. **Priority**: High, Normal, or Low based on context
4. **Assignee**: Who should handle this (default to email sender)
5. **Related Entity**: Who/what this reminder is about

Date parsing examples:
- "in 60 days" → calculate date 60 days from today
- "next Friday" → find the next Friday
- "by end of month" → last day of current month
- "follow up in Q2" → appropriate date in Q2

Be specific about what action needs to be taken.""",
            output_type=self.ReminderExtractionOutput,
            deps_type=EmailActionsEventSchema,
            model_provider=provider,
            model_name=model,
            instrument=True,
        )
    
    class ReminderExtractionOutput(BaseModel):
        reminder_text: str = Field(..., description="Clear description of what needs to be done")
        due_date_str: str = Field(..., description="Due date in ISO format or relative description")
        due_date_parsed: Optional[str] = Field(None, description="Parsed due date in ISO format")
        priority: str = Field("normal", description="Priority: high, normal, low")
        assignee_name: Optional[str] = Field(None, description="Who should handle this")
        related_entity_name: Optional[str] = Field(None, description="Related person/account")
        
        # Additional context
        reminder_type: str = Field("follow_up", description="Type: follow_up, check_in, task, deadline")
        original_context: str = Field(..., description="Context from the email")
    
    def process(self, task_context: TaskContext) -> TaskContext:
        event: EmailActionsEventSchema = task_context.event
        
        # Get classification data
        classification = task_context.nodes.get("IntentClassificationNode", {})
        initial_params = classification.get("initial_parameters", {})
        
        # Get email content
        content = event.content_for_analysis
        
        # Get today's date for relative date parsing
        today = datetime.now()
        
        # Run extraction
        result = self.agent.run_sync(
            user_prompt=f"""Extract reminder information from this email:

From: {event.from_email} ({event.from_name or 'Unknown'})
Subject: {event.subject}
Today's Date: {today.strftime('%Y-%m-%d')}

Initial context:
- Date mentioned: {initial_params.get('date', 'Not specified')}
- Content: {initial_params.get('content', 'Not specified')}

Email content:
{content}

Extract reminder details and parse any relative dates based on today's date.""",
            deps=event
        )
        
        # Parse the due date if needed
        due_date = result.output.due_date_parsed
        if not due_date and result.output.due_date_str:
            # Try to parse relative dates
            due_date_lower = result.output.due_date_str.lower()
            if "days" in due_date_lower:
                # Extract number of days
                try:
                    import re
                    days_match = re.search(r'(\d+)\s*days?', due_date_lower)
                    if days_match:
                        days = int(days_match.group(1))
                        due_date = (today + timedelta(days=days)).isoformat()
                except:
                    pass
        
        # Default assignee to sender if not specified
        assignee = result.output.assignee_name or event.from_name or event.from_email
        
        # Prepare reminder parameters
        reminder_data = {
            "reminder_text": result.output.reminder_text,
            "due_date": due_date or result.output.due_date_str,
            "priority": result.output.priority,
            "assignee": assignee,
            "related_entity_name": result.output.related_entity_name,
            "reminder_type": result.output.reminder_type,
            "original_context": result.output.original_context,
        }
        
        task_context.update_node(
            node_name=self.node_name,
            extraction_complete=True,
            reminder_parameters=reminder_data
        )
        
        return task_context