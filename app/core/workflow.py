import logging
from abc import ABC
from contextlib import contextmanager
from typing import Dict, Optional, ClassVar, Type, Any

from dotenv import load_dotenv
from opentelemetry.sdk.trace import Span

from core.langfuse_config import LangfuseConfig
from core.nodes.base import Node
from core.nodes.router import BaseRouter
from core.schema import WorkflowSchema, NodeConfig
from core.task import TaskContext
from core.validate import WorkflowValidator

load_dotenv()

"""
Workflow Orchestration Module

This module implements the core workflow functionality.
It provides a flexible framework for defining and executing workflows with multiple
nodes and routing logic.
"""


class Workflow(ABC):
    """Abstract base class for defining processing workflows.

    The Workflow class provides a framework for creating processing workflows
    with multiple nodes and routing logic. Each workflow must define its structure
    using a WorkflowSchema.

    Attributes:
        workflow_schema: Class variable defining the workflow's structure and flow
        validator: Validates the workflow schema
        nodes: Dictionary mapping node classes to their instances

    Example:
        class SupportWorkflow(Workflow):
            workflow_schema = WorkflowSchema(
                start=AnalyzeNode,
                nodes=[
                    NodeConfig(node=AnalyzeNode, connections=[RouterNode]),
                    NodeConfig(node=RouterNode, connections=[ResponseNode]),
                ]
            )
    """

    workflow_schema: ClassVar[WorkflowSchema]

    def __init__(self):
        """Initializes the workflow by validating schema and creating nodes."""
        self.validator = WorkflowValidator(self.workflow_schema)
        self.validator.validate()
        self.nodes: Dict[Type[Node], NodeConfig] = self._initialize_nodes()
        self.tracer = LangfuseConfig.get_tracer()

    @contextmanager
    def node_context(self, node_name: str):
        """Context manager for logging node execution and handling errors.

        Args:
            node_name: Name of the node being executed

        Yields:
            None

        Raises:
            Exception: Re-raises any exception that occurs during node execution
        """
        logging.info(f"Starting node: {node_name}")
        try:
            yield
        except Exception as e:
            logging.error(f"Error in node {node_name}: {str(e)}")
            raise
        finally:
            logging.info(f"Finished node: {node_name}")

    def _initialize_nodes(self) -> Dict[Type[Node], NodeConfig]:
        """Initializes all nodes defined in the workflow schema.

        Returns:
            Dictionary mapping node classes to their instances
        """
        nodes = {}
        for node_config in self.workflow_schema.nodes:
            nodes[node_config.node] = node_config
            for connected_node in node_config.connections:
                if connected_node not in nodes:
                    connected_node_config = NodeConfig(node=connected_node)
                    nodes[connected_node] = connected_node_config
        return nodes

    @staticmethod
    def _instantiate_node(node_class: Type[Node]) -> Node:
        """Creates an instance of a node class.

        Args:
            node_class: The class of the node to instantiate

        Returns:
            An instance of the specified node class
        """
        return node_class()

    def run(self, event: Any) -> TaskContext:
        """Executes the workflow for a given event.

        Args:
            event: The event to process through the workflow

        Returns:
            TaskContext containing the results of workflow execution

        Raises:
            Exception: Any exception that occurs during workflow execution
        """

        with self.tracer.start_as_current_span(
            self.__class__.__name__
        ) as workflow_span:
            task_context = TaskContext(event=event)
            task_context.metadata["nodes"] = self.nodes

            # Parse the raw event to the Pydantic schema defined in the WorkflowSchema
            task_context.event = self.workflow_schema.event_schema(**event)

            self._set_span_input(workflow_span, task_context)

            current_node_class = self.workflow_schema.start
            while current_node_class:
                with self.tracer.start_as_current_span(
                    current_node_class.__name__
                ) as node_span:
                    self._set_span_input(node_span, task_context)

                    current_node = self.nodes[current_node_class].node
                    with self.node_context(current_node_class.__name__):
                        # Process the node
                        task_context = current_node().process(task_context)

                        # Capture any prompts or model parameters that were added during processing
                        self._set_span_output(node_span, task_context)

                    # Set node-specific output
                    node_span.set_attribute(
                        "output",
                        task_context.model_dump_json(
                            include={"nodes": {current_node_class.__name__}}
                        ),
                    )

                    current_node_class = self._get_next_node_class(
                        current_node_class, task_context
                    )

            self._set_span_output(workflow_span, task_context)

            task_context.metadata.pop("nodes")

            return task_context

    def _set_span_input(self, span: Span, task_context: TaskContext):
        # Capture the basic input
        span.set_attribute(
            "input", task_context.model_dump_json(exclude={"metadata": {"nodes"}})
        )

        # Add prompt details if available in the task context
        if hasattr(task_context, "prompts"):
            span.set_attribute("prompts", str(task_context.prompts))
        if hasattr(task_context, "system_prompt"):
            span.set_attribute("system_prompt", str(task_context.system_prompt))
        if hasattr(task_context, "user_prompt"):
            span.set_attribute("user_prompt", str(task_context.user_prompt))

    def _set_span_output(self, span: Span, task_context: TaskContext):
        # Capture the basic output
        span.set_attribute(
            "output", task_context.model_dump_json(exclude={"metadata": {"nodes"}})
        )

        # Add model parameters and completion details if available
        if hasattr(task_context, "model_params"):
            span.set_attribute("model_params", str(task_context.model_params))
        if hasattr(task_context, "completion"):
            span.set_attribute("completion", str(task_context.completion))

    def _get_next_node_class(
        self, current_node_class: Type[Node], task_context: TaskContext
    ) -> Optional[Type[Node]]:
        """Determines the next node to execute in the workflow.

        Args:
            current_node_class: The class of the current node
            task_context: The current task context

        Returns:
            The class of the next node to execute, or None if at the end
        """
        node_config = next(
            (nc for nc in self.workflow_schema.nodes if nc.node == current_node_class),
            None,
        )

        if not node_config or not node_config.connections:
            return None

        if node_config.is_router:
            router: BaseRouter = self.nodes[current_node_class].node()
            return self._handle_router(router, task_context)

        return node_config.connections[0]

    def _handle_router(
        self, router: BaseRouter, task_context: TaskContext
    ) -> Optional[Type[Node]]:
        """Handles routing logic for router nodes.

        Args:
            router: The router node instance
            task_context: The current task context

        Returns:
            The class of the next node to execute, or None if at the end
        """
        next_node = router.route(task_context)
        return next_node.__class__ if next_node else None
