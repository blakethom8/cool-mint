from typing import Any, Dict

from api.schemas.event import EventSchema
from pydantic import BaseModel, Field


class TaskContext(BaseModel):
    event: EventSchema
    steps: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
