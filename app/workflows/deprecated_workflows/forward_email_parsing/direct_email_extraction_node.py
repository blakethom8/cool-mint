from typing import List, Optional
from pydantic import BaseModel, Field

from core.nodes.agent import AgentNode, AgentConfig, ModelProvider
from core.task import TaskContext
from workflows.forward_email_parsing.email_parsing_model_config import EmailParsingModelConfig
from schemas.email_parsing_schema import EmailParsingEventSchema


class DirectEmailExtractionNode(AgentNode):
    """Processes direct (non-forwarded) emails"""
    
    def get_agent_config(self) -> AgentConfig:
        return AgentConfig(
            system_prompt="""You are analyzing a direct email (not forwarded).
Extract:
1. The main purpose or intent of the email
2. Any requests or action items mentioned
3. Key topics discussed

Focus on understanding what the sender wants or is communicating.""",
            output_type=self.DirectEmailResult,
            deps_type=EmailParsingEventSchema,
            model_provider=EmailParsingModelConfig.get_provider(),
            model_name=EmailParsingModelConfig.get_model('extraction')[1],
            instrument=True,
        )
    
    class DirectEmailResult(BaseModel):
        email_purpose: str = Field(..., description="Main purpose of the email")
        has_action_required: bool = Field(..., description="Whether action is required from recipient")
        action_items: List[str] = Field(default_factory=list, description="Any action items mentioned")
        key_topics: List[str] = Field(default_factory=list, description="Key topics discussed")
    
    def process(self, task_context: TaskContext) -> TaskContext:
        event: EmailParsingEventSchema = task_context.event
        
        # Extract using LLM
        result = self.agent.run_sync(
            user_prompt=f"""Analyze this direct email:

Subject: {event.subject}
From: {event.from_email}
Body: {event.body_plain or event.body[:1000]}""",
            deps=event
        )
        
        # Store extracted data
        task_context.update_node(
            node_name=self.node_name,
            results=result.output.model_dump(),
            email_purpose=result.output.email_purpose,
            has_action_required=result.output.has_action_required
        )
        
        return task_context