from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class EmailParticipant(BaseModel):
    """Represents an email participant (sender/recipient)"""
    email: str
    name: Optional[str] = None


class Attachment(BaseModel):
    """Represents an email attachment"""
    id: str
    grant_id: str
    filename: str
    content_type: str
    size: int
    content_id: Optional[str] = None
    content_disposition: Optional[str] = None
    is_inline: bool = False


class EmailObject(BaseModel):
    """Main email object schema matching Nylas API structure"""
    id: str
    grant_id: str
    thread_id: str
    subject: Optional[str] = None
    from_: Optional[List[EmailParticipant]] = Field(None, alias="from")
    to: Optional[List[EmailParticipant]] = None
    cc: Optional[List[EmailParticipant]] = None
    bcc: Optional[List[EmailParticipant]] = None
    reply_to: Optional[List[EmailParticipant]] = None
    date: int  # Unix timestamp
    unread: bool = True
    starred: bool = False
    snippet: Optional[str] = None
    body: Optional[str] = None
    attachments: Optional[List[Attachment]] = None
    folders: Optional[List[str]] = None
    labels: Optional[List[str]] = None
    
    class Config:
        populate_by_name = True  # Allow population by field name or alias