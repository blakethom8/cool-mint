from typing import List, Type, Optional

from pydantic import BaseModel, Field

from core.nodes.base import Node

"""
Pipeline Schema Module

This module defines the schema classes used to configure pipeline structures.
It provides a type-safe way to define node connections and pipeline layouts
using Pydantic models.
"""


class NodeConfig(BaseModel):
    """Configuration model for pipeline nodes.

    NodeConfig defines the structure and behavior of a single node within
    a pipeline, including its connections to other nodes and routing properties.

    Attributes:
        node: The Node class to be instantiated
        connections: List of Node classes this node can connect to
        is_router: Flag indicating if this node performs routing logic
        description: Optional description of the node's purpose
        parallel_nodes: Optional list of Node classes that can run in parallel

    Example:
        config = NodeConfig(
            node=AnalyzeNode,
            connections=[RouterNode],
            is_router=False,
            description="Analyzes incoming requests"
            parallel_nodes=[FilterContentGuardrailNode, FilterSQLInjectionGuardrailNode]
        )
    """

    node: Type[Node]
    connections: List[Type[Node]] = Field(default_factory=list)
    is_router: bool = False
    description: Optional[str] = None
    parallel_nodes: Optional[List[Type[Node]]] = Field(default_factory=list)


class PipelineSchema(BaseModel):
    """Schema definition for a complete pipeline.

    PipelineSchema defines the overall structure of a processing pipeline,
    including its entry point and all constituent nodes.

    Attributes:
        description: Optional description of the pipeline's purpose
        event_schema: Pydantic model for validating incoming events
        start: The entry point Node class for the pipeline
        nodes: List of NodeConfig objects defining the pipeline structure

    Example:
        schema = PipelineSchema(
            description="Support ticket processing pipeline",
            start=AnalyzeNode,
            nodes=[
                NodeConfig(node=AnalyzeNode, connections=[RouterNode]),
                NodeConfig(node=RouterNode, connections=[ResponseNode, EscalateNode]),
            ]
        )
    """

    description: Optional[str] = None
    event_schema: Type[BaseModel]
    start: Type[Node]
    nodes: List[NodeConfig]
