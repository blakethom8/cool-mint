from typing import List, Optional
from pydantic import BaseModel, Field

from core.nodes.agent import AgentNode, AgentConfig, ModelProvider
from core.task import TaskContext
from workflows.forward_email_parsing.email_parsing_model_config import EmailParsingModelConfig
from schemas.email_parsing_schema import EmailParsingEventSchema


class ActionItem(BaseModel):
    task: str = Field(..., description="Description of the action item")
    deadline: Optional[str] = Field(None, description="Deadline if mentioned")
    assignee: Optional[str] = Field(None, description="Who should do this task")
    priority: str = Field("medium", description="Priority: high, medium, low")


class ActionItemExtractionNode(AgentNode):
    """Extracts action items and tasks from email content"""
    
    def get_agent_config(self) -> AgentConfig:
        return AgentConfig(
            system_prompt="""You are extracting action items and tasks from emails.
Look for:
1. Explicit tasks or to-dos
2. Follow-up items
3. Requests for action
4. Deadlines and timelines
5. Who is responsible

Consider both explicit requests and implied actions.""",
            output_type=self.ActionItemsResult,
            deps_type=EmailParsingEventSchema,
            model_provider=EmailParsingModelConfig.get_provider(),
            model_name=EmailParsingModelConfig.get_model('extraction')[1],
            instrument=True,
        )
    
    class ActionItemsResult(BaseModel):
        action_items: List[ActionItem] = Field(default_factory=list, description="All action items found")
        has_action_items: bool = Field(..., description="Whether any action items were found")
    
    def process(self, task_context: TaskContext) -> TaskContext:
        event: EmailParsingEventSchema = task_context.event
        
        # Get user request and content
        forwarded_data = task_context.nodes.get("ForwardedEmailExtractionNode", {})
        user_request = forwarded_data.get("user_request", "")
        content = forwarded_data.get("forwarded_content", "") or event.body_plain or event.body
        
        # Extract action items
        result = self.agent.run_sync(
            user_prompt=f"""Extract action items from this email:

User Request: {user_request}
Email Content: {content[:1500]}""",
            deps=event
        )
        
        # Store action items
        task_context.update_node(
            node_name=self.node_name,
            results=result.output.model_dump(),
            action_items=[item.model_dump() for item in result.output.action_items],
            has_action_items=result.output.has_action_items
        )
        
        return task_context