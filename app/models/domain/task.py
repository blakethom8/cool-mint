from enum import Enum
from typing import Any, Dict

from api.schemas.event import EventSchema
from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskContext(BaseModel):
    event: EventSchema
    parameters: Dict[str, Any] = Field(default_factory=dict)
    steps: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    skip_remaining_steps: bool = False
    status: str = TaskStatus.PENDING
