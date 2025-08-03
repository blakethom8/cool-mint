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
5. **Activity Type**: Categorize the activity type:
   - MD_to_MD_Visits: Direct physician-to-physician interactions and meetings
   - BD_Outreach: Physician liaison engagement with other stakeholders
   - Events: Group gatherings and educational sessions
   - Planning_Management: Internal planning and coordination
   - Other: General activities not fitting above categories

6. **Setting**: In-person, Virtual, Phone, etc.
7. **Key Topics**: List of key topics discussed
8. **Follow-up Items**: List of follow-up items mentioned

For MD-to-MD activities:
- Always include "MD-to-MD" in the subject
- Note which physicians were involved
- Capture key discussion points

Only capture information that is provided by the user or in the email thread. To not try to make inferences or assumptions for information that is not shared. """,
            output_type=self.CallLogExtractionOutput,
            deps_type=EmailActionsEventSchema,
            model_provider=provider,
            model_name=model,
            instrument=True,
        )
    
    class CallLogExtractionOutput(BaseModel):
        """Output schema for call log extraction"""
        
        subject: str = Field(..., description="Subject/title for the activity")
        description: str = Field(..., description="Detailed description of the activity")
        participants: List[dict] = Field(
            ..., description="List of participants with names and roles"
        )
        activity_date: Optional[str] = Field(None, description="When the activity occurred")
        activity_type: str = Field(
            ...,
            description="Type of activity (MD_to_MD_Visits, BD_Outreach, Events, Planning_Management, Other)",
        )
        meeting_setting: str = Field("In-Person", description="In-Person, Virtual, Phone")
        key_topics: List[str] = Field(
            default_factory=list, description="Key topics discussed"
        )
        follow_up_items: List[str] = Field(
            default_factory=list, description="Follow-up items mentioned"
        )
        
        # Optional fields
        is_md_to_md: bool = Field(False, description="Whether this is an MD-to-MD activity")
    
    def process(self, task_context: TaskContext) -> TaskContext:
        event: EmailActionsEventSchema = task_context.event
        
        # Get classification data
        classification = task_context.nodes.get("IntentClassificationNode", {})
        initial_params = classification.get("initial_parameters", {})
        
        # Get email content
        content = event.content
        
        # Build user prompt with optional user instruction
        user_instruction = getattr(event, 'user_instruction', '') or ''
        
        user_prompt_parts = [
            f"Extract call/meeting information from this email:",
            f"",
            f"From: {event.from_email}",
            f"Subject: {event.subject}",
        ]
        
        if user_instruction:
            user_prompt_parts.extend([
                f"",
                f"User Instruction: {user_instruction}",
            ])
        
        user_prompt_parts.extend([
            f"",
            f"Email Content:",
            f"{content}",
            f"",
            f"Extract all relevant information for logging this activity."
        ])
        
        # Run extraction
        result = self.agent.run_sync(
            user_prompt="\n".join(user_prompt_parts),
            deps=event
        )
        
        # Prepare call log parameters
        call_log_data = {
            "subject": result.output.subject,
            "description": result.output.description,
            "participants": result.output.participants,
            "activity_date": result.output.activity_date,
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