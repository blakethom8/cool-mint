from typing import Optional
from pydantic import BaseModel, Field

from core.nodes.agent import AgentNode, AgentConfig
from core.task import TaskContext
from workflows.email_actions.email_actions_model_config import EmailActionsModelConfig
from schemas.email_actions_schema import EmailActionsEventSchema, NoteParameters


class AddNoteExtractionNode(AgentNode):
    """Extracts information for adding a note"""
    
    def get_agent_config(self) -> AgentConfig:
        provider, model = EmailActionsModelConfig.get_model('extraction')
        
        return AgentConfig(
            system_prompt="""You are extracting information to create a note.

Extract the following:
1. **Note Content**: The main information to be captured as a note
2. **Related Entity**: Who or what this note is about (person, account, opportunity)
3. **Note Type**: General, Meeting Notes, Follow-up, Important Information

Focus on:
- Capturing the key information the user wants documented
- Identifying the main subject/entity the note relates to
- Preserving important details and context
- Formatting the note content clearly

If the email contains a thread or meeting notes, structure them clearly.""",
            output_type=self.NoteExtractionOutput,
            deps_type=EmailActionsEventSchema,
            model_provider=provider,
            model_name=model,
            instrument=True,
        )
    
    class NoteExtractionOutput(BaseModel):
        note_content: str = Field(..., description="The formatted note content")
        related_entity_name: Optional[str] = Field(None, description="Name of person/account this relates to")
        related_entity_type: str = Field("contact", description="Type: contact, account, opportunity")
        note_type: str = Field("general", description="Type of note: general, meeting, follow_up, important")
        
        # Additional context
        key_points: list[str] = Field(default_factory=list, description="Key points from the note")
        mentioned_entities: list[str] = Field(default_factory=list, description="Other people/accounts mentioned")
    
    def process(self, task_context: TaskContext) -> TaskContext:
        event: EmailActionsEventSchema = task_context.event
        
        # Get classification data
        classification = task_context.nodes.get("IntentClassificationNode", {})
        initial_params = classification.get("initial_parameters", {})
        
        # Get email content
        content = event.content_for_analysis
        
        # Run extraction
        result = self.agent.run_sync(
            user_prompt=f"""Extract note information from this email:

From: {event.from_email}
Subject: {event.subject}

Initial context:
- Content preview: {initial_params.get('content', 'Not specified')}
- People mentioned: {initial_params.get('participants', [])}

Email content:
{content}

Create a well-formatted note capturing the key information.""",
            deps=event
        )
        
        # Prepare note parameters
        note_data = {
            "note_content": result.output.note_content,
            "related_entity_name": result.output.related_entity_name,
            "related_entity_type": result.output.related_entity_type,
            "note_type": result.output.note_type,
            "key_points": result.output.key_points,
            "mentioned_entities": result.output.mentioned_entities,
        }
        
        task_context.update_node(
            node_name=self.node_name,
            extraction_complete=True,
            note_parameters=note_data
        )
        
        return task_context