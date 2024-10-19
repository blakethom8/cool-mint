import logging
from abc import ABC
from contextlib import contextmanager
from typing import Dict, List, Type, Optional, Set

from pydantic import BaseModel

from api.event_schema import EventSchema
from core.task import TaskContext
from core.base import Step
from core.router import BaseRouter

StepType = Type[Step]


class StepConfig(BaseModel):
    next: Optional[StepType] = None
    routes: Optional[Dict[str, StepType]] = None
    end: bool = False


class PipelineSchema(BaseModel):
    start: StepType
    steps: Dict[str, StepConfig]
    end_steps: Set[str] = set()

    def __init__(self, **data):
        super().__init__(**data)
        self._update_end_steps()

    def _update_end_steps(self):
        """Update the end_steps set based on the step configurations."""
        self.end_steps = {
            step_name
            for step_name, config in self.steps.items()
            if config.end or (config.next is None and not config.routes)
        }


class Pipeline(ABC):
    """Base class for all pipelines.

    Attributes:
        pipeline_schema: The schema defining the pipeline structure.
        steps: A list of initialized pipeline steps.
    """

    pipeline_schema: PipelineSchema
    steps: List[Step] = []

    @contextmanager
    def step_context(self, step_name: str):
        """Context manager for logging step execution."""
        logging.info(f"Starting step: {step_name}")
        try:
            yield
        except Exception as e:
            logging.error(f"Error in step {step_name}: {str(e)}")
            raise
        finally:
            logging.info(f"Finished step: {step_name}")

    def initialize_steps(self):
        """Initialize the pipeline steps."""
        self.steps = []
        current_step = self.pipeline_schema.start
        while current_step:
            self.steps.append(current_step())
            if issubclass(current_step, BaseRouter):
                break
            current_step = self.pipeline_schema.steps[current_step.__name__].next

    def run(self, event: EventSchema) -> TaskContext:
        task_context = TaskContext(event=event, pipeline=self)
        current_step = self.steps[0]

        while current_step:
            with self.step_context(current_step.step_name):
                task_context = current_step.process(task_context)

            current_step = self._get_next_step(current_step, task_context)

        return task_context

    def _get_next_step(
        self, current_step: Step, task_context: TaskContext
    ) -> Optional[Step]:
        step_config = self.pipeline_schema.steps[current_step.__class__.__name__]

        if (
            step_config.end
            or current_step.__class__.__name__ in self.pipeline_schema.end_steps
        ):
            return None

        if isinstance(current_step, BaseRouter):
            return self._handle_router(current_step, step_config, task_context)

        return step_config.next() if step_config.next else None

    def _handle_router(
        self, router: BaseRouter, router_config: StepConfig, task_context: TaskContext
    ) -> Optional[Step]:
        route_result = router.route(task_context)
        if (
            not route_result
            or route_result.__class__.__name__ not in router_config.routes
        ):
            return None
        next_step_class = router_config.routes[route_result.__class__.__name__]
        return next_step_class()
