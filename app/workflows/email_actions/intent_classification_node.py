from typing import Optional
from pydantic import BaseModel, Field

from core.nodes.agent import AgentNode, AgentConfig
from core.task import TaskContext
from workflows.email_actions.email_actions_model_config import EmailActionsModelConfig
from schemas.email_actions_schema import EmailActionsEventSchema, ActionClassification


class IntentClassificationNode(AgentNode):
    """Classifies the intent of an email into specific actions"""
    
    def get_agent_config(self) -> AgentConfig:
        provider, model = EmailActionsModelConfig.get_model('classification')
        
        return AgentConfig(
            system_prompt="""You are an AI assistant that classifies emails into specific action types.
            
Analyze the email content and determine which ONE primary action the user is requesting:

1. **add_note**: User wants to capture information, thoughts, or meeting notes
   - Keywords: "capture notes", "document", "record information", "make a note"
   - Example: "capture the notes from this thread"

2. **log_call**: User wants to log a call, meeting, or MD-to-MD activity
   - Keywords: "log activity", "log call", "log meeting", "MD-to-MD", "capture meeting"
   - Example: "log an MD-to-MD activity with Dr. McDonald"

3. **set_reminder**: User wants to create a reminder or follow-up task
   - Keywords: "remind me", "follow up", "check back", "schedule reminder"
   - Example: "remind me to follow up with them in 60 days"

If multiple actions could apply, choose the PRIMARY/MAIN action being requested.
If no clear action matches, use "unknown".

Provide clear reasoning for your classification and extract initial parameters.""",
            output_type=self.IntentClassificationOutput,
            deps_type=EmailActionsEventSchema,
            model_provider=provider,
            model_name=model,
            instrument=True,
        )
    
    class IntentClassificationOutput(BaseModel):
        action_type: str = Field(..., description="One of: add_note, log_call, set_reminder, unknown")
        confidence_score: float = Field(..., description="Confidence in classification (0-1)")
        reasoning: str = Field(..., description="Explanation of why this classification was chosen")
        
        # Initial parameter extraction
        extracted_subject: Optional[str] = Field(None, description="Subject/title if mentioned")
        extracted_participants: Optional[list[str]] = Field(None, description="People mentioned")
        extracted_date: Optional[str] = Field(None, description="Date/time mentioned")
        extracted_content: Optional[str] = Field(None, description="Main content to capture")
    
    def process(self, task_context: TaskContext) -> TaskContext:
        event: EmailActionsEventSchema = task_context.event
        
        # Get the content to analyze
        content = event.content
        
        if not content:
            # No content to analyze
            task_context.update_node(
                node_name=self.node_name,
                action_type="unknown",
                confidence_score=0.0,
                reasoning="No email content available to analyze",
                error="No content found"
            )
            return task_context
        
        # Run classification
        result = self.agent.run_sync(
            user_prompt=f"""Classify this email request:

From: {event.from_email}
Subject: {event.subject}

Content:
{content}

Determine the primary action being requested and extract any relevant parameters.""",
            deps=event
        )
        
        # Store classification results
        classification_data = {
            "action_type": result.output.action_type,
            "confidence_score": result.output.confidence_score,
            "reasoning": result.output.reasoning,
            "initial_parameters": {
                "subject": result.output.extracted_subject,
                "participants": result.output.extracted_participants,
                "date": result.output.extracted_date,
                "content": result.output.extracted_content,
            }
        }
        
        task_context.update_node(
            node_name=self.node_name,
            **classification_data
        )
        
        return task_context