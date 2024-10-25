import logging
from abc import ABC
from contextlib import contextmanager
from typing import Dict, Optional, ClassVar, Type

from api.event_schema import EventSchema
from core.base import Step
from core.router import BaseRouter
from core.schema import PipelineSchema
from core.task import TaskContext
from core.validate import PipelineValidator


class Pipeline(ABC):
    """Base class for all pipelines.

    Attributes:
        pipeline_schema: The schema defining the pipeline structure.
    """

    pipeline_schema: ClassVar[PipelineSchema]

    def __init__(self):
        self.validator = PipelineValidator(self.pipeline_schema)
        self.validator.validate()
        self.nodes: Dict[Type[Step], Step] = self._initialize_nodes()

    @contextmanager
    def node_context(self, node_name: str):
        """Context manager for logging node execution."""
        logging.info(f"Starting node: {node_name}")
        try:
            yield
        except Exception as e:
            logging.error(f"Error in node {node_name}: {str(e)}")
            raise
        finally:
            logging.info(f"Finished node: {node_name}")

    def _initialize_nodes(self) -> Dict[Type[Step], Step]:
        """Initialize the pipeline nodes."""
        return {
            node_config.node: self._instantiate_node(node_config.node)
            for node_config in self.pipeline_schema.nodes
        }

    @staticmethod
    def _instantiate_node(node_class: Type[Step]) -> Step:
        """Instantiate a single node."""
        return node_class()

    def run(self, event: EventSchema) -> TaskContext:
        """Run the pipeline."""
        task_context = TaskContext(event=event, pipeline=self)
        current_node_class = self.pipeline_schema.start

        while current_node_class:
            current_node = self.nodes[current_node_class]
            with self.node_context(current_node_class.__name__):
                task_context = current_node.process(task_context)
            current_node_class = self._get_next_node_class(
                current_node_class, task_context
            )

        return task_context

    def _get_next_node_class(
        self, current_node_class: Type[Step], task_context: TaskContext
    ) -> Optional[Type[Step]]:
        """Determine the next node in the pipeline."""
        node_config = next(
            (nc for nc in self.pipeline_schema.nodes if nc.node == current_node_class),
            None,
        )

        if not node_config or not node_config.connections:
            return None

        if node_config.is_router:
            return self._handle_router(self.nodes[current_node_class], task_context)

        return node_config.connections[0]

    def _handle_router(
        self, router: BaseRouter, task_context: TaskContext
    ) -> Optional[Type[Step]]:
        """Handle routing logic for router nodes."""
        next_node = router.route(task_context)
        return next_node.__class__ if next_node else None
