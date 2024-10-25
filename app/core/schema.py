from typing import Dict, List, Type

from core.base import Step
from pydantic import BaseModel, Field


class StepConfig(BaseModel):
    step: Type[Step]
    next: List[str] = Field(default_factory=list)
    is_router: bool = False


class PipelineSchema(BaseModel):
    start: str
    steps: Dict[str, StepConfig]
