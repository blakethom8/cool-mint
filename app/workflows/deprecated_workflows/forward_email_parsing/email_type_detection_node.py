from typing import Optional
from pydantic import BaseModel, Field
from pydantic_ai import RunContext

from core.nodes.agent import AgentNode, AgentConfig, ModelProvider
from core.nodes.router import BaseRouter
from core.task import TaskContext
from workflows.forward_email_parsing.email_parsing_model_config import EmailParsingModelConfig
from schemas.email_parsing_schema import EmailParsingEventSchema


class EmailTypeDetectionNode(AgentNode, BaseRouter):
    """Detects email type and routes to appropriate extraction path"""
    
    def get_agent_config(self) -> AgentConfig:
        return AgentConfig(
            system_prompt="""You are an email classifier that determines the type and intent of emails.
            
Classify emails into one of these types:
1. forwarded_request: A forwarded email where the sender is asking an AI assistant to take action
2. direct_email: A regular email sent directly to the recipient
3. auto_reply: An automated response or system-generated email

For forwarded emails, look for:
- Forwarding indicators like "Fwd:", "---------- Forwarded message ---------"
- User instructions or requests before the forwarded content
- Language asking for help, action, or processing

Provide your classification with confidence score.""",
            output_type=self.EmailTypeResult,
            deps_type=EmailParsingEventSchema,
            model_provider=EmailParsingModelConfig.get_provider(),
            model_name=EmailParsingModelConfig.get_model('classification')[1],
            instrument=True,
        )
    
    class EmailTypeResult(BaseModel):
        email_type: str = Field(..., description="Type of email: forwarded_request, direct_email, or auto_reply")
        is_forwarded: bool = Field(..., description="Whether this is a forwarded email")
        has_user_request: bool = Field(..., description="Whether there's a user request for AI action")
        confidence: float = Field(..., description="Confidence score between 0 and 1")
        reasoning: str = Field(..., description="Brief explanation of the classification")
    
    def process(self, task_context: TaskContext) -> TaskContext:
        event: EmailParsingEventSchema = task_context.event
        
        # Prepare the email content for classification
        email_preview = f"""
Subject: {event.subject}
From: {event.from_email} ({event.from_name or 'No name'})
To: {', '.join(event.to_emails)}

Body Preview:
{event.snippet or event.body[:500]}
"""
        
        # Run the classification
        result = self.agent.run_sync(
            user_prompt=f"Classify this email:\n\n{email_preview}",
            deps=event
        )
        
        # Store results
        task_context.update_node(
            node_name=self.node_name,
            results=result.output.model_dump(),
            email_type=result.output.email_type,
            is_forwarded=result.output.is_forwarded
        )
        
        return task_context
    
    def route(self, task_context: TaskContext):
        """Route based on email type"""
        from workflows.forward_email_parsing.forwarded_email_extraction_node import ForwardedEmailExtractionNode
        from workflows.forward_email_parsing.direct_email_extraction_node import DirectEmailExtractionNode
        
        node_data = task_context.nodes.get(self.node_name, {})
        email_type = node_data.get("email_type")
        
        if email_type == "forwarded_request":
            return ForwardedEmailExtractionNode()
        else:
            return DirectEmailExtractionNode()