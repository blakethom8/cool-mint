from typing import Optional

from pydantic import BaseModel

"""
Event Schema Module

This module defines the Pydantic models that FastAPI uses to validate incoming
HTTP requests. It specifies the expected structure and validation rules for
events entering the system through the API endpoints.
"""


class DefaultEventSchema(BaseModel):
    event_id: str
    event_type: str
    source: Optional[str] = None
