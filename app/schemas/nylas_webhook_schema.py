from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class WebhookDelta(BaseModel):
    """Represents a single change/delta in a webhook notification"""
    type: str  # e.g., "message.created", "message.updated"
    object: str  # e.g., "message"
    object_data: Dict[str, Any]  # The actual email/message data
    grant_id: str


class WebhookEvent(BaseModel):
    """Main webhook event schema from Nylas"""
    specversion: str = "1.0"
    type: str  # e.g., "message.created"
    source: str  # e.g., "https://api.nylas.com"
    id: str  # Event ID
    time: int  # Unix timestamp
    webhook_delivery_attempt: int
    deltas: List[WebhookDelta]
    
    @property
    def data(self) -> Dict[str, Any]:
        """Legacy property for backward compatibility"""
        if self.deltas:
            return {
                "object": self.deltas[0].object_data,
                "type": self.deltas[0].type,
                "grant_id": self.deltas[0].grant_id
            }
        return {}


class WebhookChallenge(BaseModel):
    """Schema for webhook verification challenge"""
    challenge: str