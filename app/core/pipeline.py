import logging
from abc import ABC
from contextlib import contextmanager
from typing import Dict, Optional, ClassVar

from api.event_schema import EventSchema
from core.base import Step
from core.router import BaseRouter
from core.schema import PipelineSchema, StepConfig
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
        self.steps: Dict[str, Step] = self._initialize_steps()

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

    def _initialize_steps(self) -> Dict[str, Step]:
        """Initialize the pipeline steps."""
        return {
            step_name: self._instantiate_step(step_config)
            for step_name, step_config in self.pipeline_schema.steps.items()
        }

    @staticmethod
    def _instantiate_step(step_config: StepConfig) -> Step:
        """Instantiate a single step."""
        return step_config.step()

    def run(self, event: EventSchema) -> TaskContext:
        """Run the pipeline."""
        task_context = TaskContext(event=event, pipeline=self)
        current_step_name = self.pipeline_schema.start

        while current_step_name:
            current_step = self.steps[current_step_name]
            with self.step_context(current_step_name):
                task_context = current_step.process(task_context)
            current_step_name = self._get_next_step_name(
                current_step_name, task_context
            )

        return task_context

    def _get_next_step_name(
        self, current_step_name: str, task_context: TaskContext
    ) -> Optional[str]:
        """Determine the next step in the pipeline."""
        step_config = self.pipeline_schema.steps[current_step_name]

        if not step_config.next:
            return None

        if step_config.is_router:
            return self._handle_router(self.steps[current_step_name], task_context)

        return step_config.next[0]

    def _handle_router(
        self, router: BaseRouter, task_context: TaskContext
    ) -> Optional[str]:
        """Handle routing logic for router steps."""
        next_step = router.route(task_context)
        return next_step.step_name if next_step else None
