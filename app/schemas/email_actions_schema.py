from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime


class EmailActionsEventSchema(BaseModel):
    """Event schema for email actions workflow"""
    
    # Email identification
    email_id: str = Field(..., description="ID of the email to process")
    
    # Email content
    content: str = Field(..., description="Email content to analyze")
    subject: str = Field(..., description="Email subject")
    from_email: str = Field(..., description="Sender email address")
    
    # Enhanced fields for forwarded emails
    is_forwarded: bool = Field(False, description="Whether email is forwarded")
    user_instruction: Optional[str] = Field(None, description="User's request (for forwarded emails)")
    
    # Processing directives
    force_reprocess: bool = Field(False, description="Force reprocessing even if already processed")
    allowed_actions: Optional[List[str]] = Field(
        default=['add_note', 'log_call', 'set_reminder'],
        description="Which actions to consider"
    )
    


class ActionClassification(BaseModel):
    """Result of intent classification"""
    
    action_type: str = Field(..., description="Type of action: add_note, log_call, set_reminder")
    confidence_score: float = Field(..., description="Confidence score 0-1")
    reasoning: str = Field(..., description="Explanation of classification")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Initial parameters extracted")


class CallLogParameters(BaseModel):
    """Parameters for log_call action"""
    
    subject: str = Field(..., description="Subject of the call/meeting")
    description: str = Field(..., description="Description of what was discussed")
    participants: List[str] = Field(..., description="People involved")
    activity_date: Optional[datetime] = Field(None, description="When the activity occurred")
    duration_minutes: Optional[int] = Field(None, description="Duration in minutes")
    activity_type: Optional[str] = Field(None, description="Type of activity (MD-to-MD, etc)")
    meeting_setting: Optional[str] = Field(None, description="In-person, Virtual, etc")


class NoteParameters(BaseModel):
    """Parameters for add_note action"""
    
    note_content: str = Field(..., description="Content of the note")
    related_entity: Optional[str] = Field(None, description="Who/what this note is about")
    note_type: Optional[str] = Field('general', description="Type of note")


class ReminderParameters(BaseModel):
    """Parameters for set_reminder action"""
    
    reminder_text: str = Field(..., description="What to be reminded about")
    due_date: datetime = Field(..., description="When the reminder is due")
    assignee: Optional[str] = Field(None, description="Who should handle this")
    priority: str = Field('normal', description="Priority level")
    related_entity: Optional[str] = Field(None, description="Related contact/account")