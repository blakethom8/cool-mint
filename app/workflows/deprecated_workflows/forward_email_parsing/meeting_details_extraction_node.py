from typing import List, Optional, Dict
from pydantic import BaseModel, Field

from core.nodes.agent import AgentNode, AgentConfig, ModelProvider
from core.task import TaskContext
from workflows.forward_email_parsing.email_parsing_model_config import EmailParsingModelConfig
from schemas.email_parsing_schema import EmailParsingEventSchema


class MeetingDetailsExtractionNode(AgentNode):
    """Extracts meeting-specific information if the email is about a meeting"""
    
    def get_agent_config(self) -> AgentConfig:
        return AgentConfig(
            system_prompt="""You are analyzing emails for meeting-related information.
If the email discusses a meeting, extract:
1. Meeting type (lunch, conference call, in-person, etc.)
2. Attendees and their roles
3. Meeting date/time
4. Topics discussed or agenda
5. Location (if mentioned)

If this is not about a meeting, indicate that clearly.""",
            output_type=self.MeetingDetails,
            deps_type=EmailParsingEventSchema,
            model_provider=EmailParsingModelConfig.get_provider(),
            model_name=EmailParsingModelConfig.get_model('extraction')[1],
            instrument=True,
        )
    
    class MeetingDetails(BaseModel):
        is_meeting_related: bool = Field(..., description="Whether this email is about a meeting")
        meeting_type: Optional[str] = Field(None, description="Type of meeting")
        attendees: List[Dict[str, str]] = Field(default_factory=list, description="Meeting attendees with roles")
        meeting_date: Optional[str] = Field(None, description="Meeting date/time")
        topics: List[str] = Field(default_factory=list, description="Topics discussed or planned")
        location: Optional[str] = Field(None, description="Meeting location")
    
    def process(self, task_context: TaskContext) -> TaskContext:
        event: EmailParsingEventSchema = task_context.event
        
        # Get content from previous nodes
        forwarded_data = task_context.nodes.get("ForwardedEmailExtractionNode", {})
        entity_data = task_context.nodes.get("EntityExtractionNode", {})
        
        content = forwarded_data.get("forwarded_content", "") or event.body_plain or event.body
        people = entity_data.get("people", [])
        
        # Extract meeting details
        result = self.agent.run_sync(
            user_prompt=f"""Extract meeting details from this email:

Subject: {event.subject}
People mentioned: {[p['name'] for p in people]}
Content: {content[:1500]}""",
            deps=event
        )
        
        # Store meeting info
        if result.output.is_meeting_related:
            task_context.update_node(
                node_name=self.node_name,
                results=result.output.model_dump(),
                meeting_info={
                    "type": result.output.meeting_type,
                    "attendees": result.output.attendees,
                    "date": result.output.meeting_date,
                    "topics": result.output.topics,
                    "location": result.output.location
                }
            )
        else:
            task_context.update_node(
                node_name=self.node_name,
                results=result.output.model_dump(),
                meeting_info=None
            )
        
        return task_context