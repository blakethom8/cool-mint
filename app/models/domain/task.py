from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from api.schemas.event import EventSchema
from models.domain.result import TaskResult


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
    result: Optional[TaskResult] = None
