from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field


class EmailParsingEventSchema(BaseModel):
    """Schema for email parsing workflow events"""
    
    # Email identifier
    email_id: UUID = Field(..., description="UUID of the email to parse")
    
    # Email basic info
    subject: str = Field(..., description="Email subject line")
    from_email: str = Field(..., description="Sender email address")
    from_name: Optional[str] = Field(None, description="Sender name")
    to_emails: List[str] = Field(..., description="Recipient email addresses")
    
    # Email content
    body: str = Field(..., description="Full HTML email body")
    body_plain: Optional[str] = Field(None, description="Plain text email body")
    snippet: Optional[str] = Field(None, description="Email preview snippet")
    
    # Email metadata
    date: int = Field(..., description="Unix timestamp when email was sent")
    thread_id: str = Field(..., description="Email thread identifier")
    nylas_id: str = Field(..., description="Nylas email identifier")
    
    # Processing flags
    force_reparse: bool = Field(False, description="Force re-parsing even if already parsed")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email_id": "123e4567-e89b-12d3-a456-426614174000",
                "subject": "Fwd: Ortho Lunch",
                "from_email": "blakethomson8@gmail.com",
                "from_name": "Blake Thomson",
                "to_emails": ["thomsonblakecrm@gmail.com"],
                "body": "<html>...</html>",
                "snippet": "Chat, below is an email thread...",
                "date": 1737834223,
                "thread_id": "thread_123",
                "nylas_id": "nylas_456"
            }
        }