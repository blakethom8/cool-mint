from typing import List, Dict, Optional
from pydantic import BaseModel, Field
import re

from core.nodes.agent import AgentNode, AgentConfig, ModelProvider
from core.task import TaskContext
from workflows.forward_email_parsing.email_parsing_model_config import EmailParsingModelConfig
from schemas.email_parsing_schema import EmailParsingEventSchema


class ForwardedEmailExtractionNode(AgentNode):
    """Extracts user request and forwarded content from forwarded emails"""
    
    def get_agent_config(self) -> AgentConfig:
        return AgentConfig(
            system_prompt="""You are an expert at parsing forwarded emails to extract:
1. The user's request or instructions (what they want the AI to do)
2. The forwarded email metadata (original sender, date, subject)
3. The forwarded email content

Look for patterns like:
- User instructions before "---------- Forwarded message ---------"
- Intent keywords: "log", "schedule", "create", "add", "capture", "extract"
- Original email headers in the forwarded section

Extract and structure this information clearly.""",
            output_type=self.ForwardedEmailResult,
            deps_type=EmailParsingEventSchema,
            model_provider=EmailParsingModelConfig.get_provider(),
            model_name=EmailParsingModelConfig.get_model('extraction')[1],
            instrument=True,
        )
    
    class ForwardedEmailResult(BaseModel):
        user_request: str = Field(..., description="The user's request or instructions")
        request_intents: List[str] = Field(..., description="Identified intents like 'log_activity', 'schedule_meeting'")
        forwarded_from: Dict[str, str] = Field(..., description="Original sender info: email, name, date, subject")
        forwarded_content: str = Field(..., description="The main content of the forwarded email")
        original_thread_id: Optional[str] = Field(None, description="Original email thread ID if found")
    
    def process(self, task_context: TaskContext) -> TaskContext:
        event: EmailParsingEventSchema = task_context.event
        
        # Extract using LLM
        result = self.agent.run_sync(
            user_prompt=f"""Extract the user request and forwarded email content from this email:

Subject: {event.subject}
Body: {event.body_plain or event.body}""",
            deps=event
        )
        
        # Store extracted data
        task_context.update_node(
            node_name=self.node_name,
            results=result.output.model_dump(),
            user_request=result.output.user_request,
            request_intents=result.output.request_intents,
            forwarded_metadata=result.output.forwarded_from
        )
        
        return task_context