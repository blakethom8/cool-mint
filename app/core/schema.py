from typing import List, Type, Optional
from core.base import Node
from pydantic import BaseModel, Field


class NodeConfig(BaseModel):
    node: Type[Node]
    connections: List[Type[Node]] = Field(default_factory=list)
    is_router: bool = False
    description: Optional[str] = None


class PipelineSchema(BaseModel):
    description: Optional[str] = None
    start: Type[Node]
    nodes: List[NodeConfig]
