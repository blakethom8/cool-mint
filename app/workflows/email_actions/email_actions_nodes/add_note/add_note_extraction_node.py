from typing import Optional, List, Dict
from pydantic import BaseModel, Field

from core.nodes.agent import AgentNode, AgentConfig
from core.task import TaskContext
from workflows.email_actions.email_actions_model_config import EmailActionsModelConfig
from schemas.email_actions_schema import EmailActionsEventSchema, NoteParameters


class AddNoteExtractionNode(AgentNode):
    """Extracts information for adding a note with LLM analysis"""
    
    def get_agent_config(self) -> AgentConfig:
        provider, model = EmailActionsModelConfig.get_model('extraction')
        
        return AgentConfig(
            system_prompt="""You are extracting information to create a note with comprehensive analysis.

Extract the following:
1. **Note Content**: The main information to be captured as a note (well-formatted and complete)
2. **All Mentioned Entities**: Extract ALL people, organizations, or accounts mentioned in the email
3. **Topics**: Key topics/themes discussed (e.g., ['referral patterns', 'patient care', 'new program'])
4. **Sentiment**: Overall sentiment of the communication (Positive, Negative, Neutral, Mixed)
5. **Note Type**: General, Meeting Notes, Follow-up, Important Information

For entities, extract:
- Full names of all people mentioned (e.g., "Dr. John Smith", "Sarah Johnson")
- Organization names (e.g., "Cedars-Sinai", "UCLA Medical Center")
- Any other relevant entities (departments, programs, etc.)

Important:
- Extract ALL entities mentioned, not just the primary one
- Preserve exact names as mentioned in the email
- Topics should be concise phrases (2-4 words each)
- Sentiment should reflect the overall tone and context

If the email contains a thread or meeting notes, structure them clearly in the note content.""",
            output_type=self.NoteExtractionOutput,
            deps_type=EmailActionsEventSchema,
            model_provider=provider,
            model_name=model,
            instrument=True,
        )
    
    class NoteExtractionOutput(BaseModel):
        """Enhanced output with LLM analysis fields"""
        note_content: str = Field(..., description="The formatted note content")
        note_type: str = Field("general", description="Type of note: general, meeting, follow_up, important")
        
        # All entities mentioned (for entity matching)
        mentioned_entities: List[Dict[str, str]] = Field(
            default_factory=list,
            description="All entities mentioned: [{'name': 'Dr. Smith', 'type': 'contact'}, ...]"
        )
        
        # LLM analysis fields
        topics: List[str] = Field(
            default_factory=list,
            description="Key topics discussed (e.g., ['patient referral', 'new protocol'])"
        )
        sentiment: str = Field(
            "Neutral",
            description="Overall sentiment: Positive, Negative, Neutral, Mixed"
        )
        
        # Additional context
        key_points: List[str] = Field(default_factory=list, description="Key points from the note")
        
        # Primary entity (if clear from context)
        primary_entity_name: Optional[str] = Field(None, description="Primary entity this note is about")
        primary_entity_type: str = Field("contact", description="Type: contact, account, opportunity")
    
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
            f"Extract note information from this email:",
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
            f"Create a comprehensive note with all entities, topics, and sentiment analysis."
        ])
        
        # Run extraction
        result = self.agent.run_sync(
            user_prompt="\n".join(user_prompt_parts),
            deps=event
        )
        
        # Prepare enhanced note parameters
        note_data = {
            "note_content": result.output.note_content,
            "note_type": result.output.note_type,
            "mentioned_entities": result.output.mentioned_entities,
            "topics": result.output.topics,
            "sentiment": result.output.sentiment,
            "key_points": result.output.key_points,
            "primary_entity_name": result.output.primary_entity_name,
            "primary_entity_type": result.output.primary_entity_type,
        }
        
        task_context.update_node(
            node_name=self.node_name,
            extraction_complete=True,
            note_parameters=note_data
        )
        
        return task_context