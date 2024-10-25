from typing import List, Type, Optional
from core.base import Step
from pydantic import BaseModel, Field


class StepConfig(BaseModel):
    node: Type[Step]
    connections: List[Type[Step]] = Field(default_factory=list)
    is_router: bool = False
    is_end: bool = False
    description: Optional[str] = None


class PipelineSchema(BaseModel):
    description: Optional[str] = None
    start: Type[Step]
    nodes: List[StepConfig]
