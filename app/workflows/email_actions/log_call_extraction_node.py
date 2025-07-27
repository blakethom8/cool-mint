from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from core.nodes.agent import AgentNode, AgentConfig
from core.task import TaskContext
from workflows.email_actions.email_actions_model_config import EmailActionsModelConfig
from schemas.email_actions_schema import EmailActionsEventSchema, CallLogParameters


class LogCallExtractionNode(AgentNode):
    """Extracts detailed information for logging a call/meeting activity"""
    
    def get_agent_config(self) -> AgentConfig:
        provider, model = EmailActionsModelConfig.get_model('extraction')
        
        return AgentConfig(
            system_prompt="""You are extracting information to log a call, meeting, or activity.

Extract the following information:
1. **Subject**: Brief title for the activity (e.g., "MD-to-MD Lunch with Dr. McDonald")
2. **Description**: Detailed notes about what was discussed
3. **Participants**: All people involved (extract names and roles)
4. **Date**: When the activity occurred (if mentioned)
5. **Duration**: How long it lasted (if mentioned)
6. **Activity Type**: Type of activity (MD-to-MD, Sales Call, etc.)
7. **Setting**: In-person, Virtual, Phone, etc.

For MD-to-MD activities:
- Always include "MD-to-MD" in the subject
- Note which physicians were involved
- Capture key discussion points

Be thorough in extracting discussion topics, action items, and follow-up plans.""",
            output_type=self.CallLogExtractionOutput,
            deps_type=EmailActionsEventSchema,
            model_provider=provider,
            model_name=model,
            instrument=True,
        )
    
    class CallLogExtractionOutput(BaseModel):
        subject: str = Field(..., description="Subject/title for the activity")
        description: str = Field(..., description="Detailed description of the activity")
        participants: List[dict] = Field(..., description="List of participants with names and roles")
        activity_date: Optional[str] = Field(None, description="When the activity occurred")
        duration_minutes: Optional[int] = Field(None, description="Duration in minutes")
        activity_type: str = Field(..., description="Type of activity (MD-to-MD, Sales Call, etc)")
        meeting_setting: str = Field("In-Person", description="In-Person, Virtual, Phone")
        
        # Specific fields for medical activities
        is_md_to_md: bool = Field(False, description="Whether this is an MD-to-MD activity")
        key_topics: List[str] = Field(default_factory=list, description="Key topics discussed")
        follow_up_items: List[str] = Field(default_factory=list, description="Follow-up items mentioned")
    
    def process(self, task_context: TaskContext) -> TaskContext:
        event: EmailActionsEventSchema = task_context.event
        
        # Get classification data
        classification = task_context.nodes.get("IntentClassificationNode", {})
        initial_params = classification.get("initial_parameters", {})
        
        # Get email content
        content = event.content
        
        # Run extraction
        result = self.agent.run_sync(
            user_prompt=f"""Extract call/meeting information from this email:

From: {event.from_email}
Subject: {event.subject}

Initial extraction hints:
- Participants mentioned: {initial_params.get('participants', [])}
- Date mentioned: {initial_params.get('date', 'Not specified')}

Email content:
{content}

Extract all relevant information for logging this activity.""",
            deps=event
        )
        
        # Prepare call log parameters
        call_log_data = {
            "subject": result.output.subject,
            "description": result.output.description,
            "participants": result.output.participants,
            "activity_date": result.output.activity_date,
            "duration_minutes": result.output.duration_minutes,
            "activity_type": result.output.activity_type,
            "meeting_setting": result.output.meeting_setting,
            "is_md_to_md": result.output.is_md_to_md,
            "key_topics": result.output.key_topics,
            "follow_up_items": result.output.follow_up_items,
        }
        
        # Determine MNO type and subtype based on activity
        if result.output.is_md_to_md:
            call_log_data["mno_type"] = "MD_to_MD_Visits"
            call_log_data["mno_subtype"] = "MD_to_MD_w_Cedars" if "cedars" in content.lower() else "MD_to_MD_General"
        else:
            call_log_data["mno_type"] = "BD_Outreach"
            call_log_data["mno_subtype"] = "General_Meeting"
        
        call_log_data["mno_setting"] = result.output.meeting_setting
        
        task_context.update_node(
            node_name=self.node_name,
            extraction_complete=True,
            call_log_parameters=call_log_data
        )
        
        return task_context