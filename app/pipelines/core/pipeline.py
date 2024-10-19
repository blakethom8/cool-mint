import logging
from abc import ABC
from contextlib import contextmanager
from typing import Dict, List, Type, Optional

from pydantic import BaseModel

from api.schemas.event import EventSchema
from models.domain.task import TaskContext, TaskStatus
from pipelines.core.base import BaseStep
from pipelines.core.router import BaseRouter

StepType = Type[BaseStep]


class StepConfig(BaseModel):
    next: Optional[StepType] = None
    routes: Optional[Dict[str, StepType]] = None


class PipelineSchema(BaseModel):
    start: StepType
    steps: Dict[str, StepConfig]


class BasePipeline(ABC):
    """Base class for all pipelines.

    Attributes:
        pipeline_schema: The schema defining the pipeline structure.
        steps: A list of initialized pipeline steps.
    """

    pipeline_schema: PipelineSchema
    steps: List[BaseStep] = []

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

    def get_next_step(self, current_step: BaseStep) -> Optional[StepType]:
        """Get the next step in the pipeline."""
        step_name = current_step.__class__.__name__
        if isinstance(current_step, BaseRouter):
            return None
        return self.pipeline_schema.steps[step_name].next

    def run(self, event: EventSchema) -> TaskContext:
        """Run the pipeline for a given event."""
        task_result = TaskContext(event=event, status=TaskStatus.RUNNING)
        current_step = self.steps[0]

        while current_step:
            with self.step_context(current_step.step_name):
                task_result = current_step.process(task_result)

            if isinstance(current_step, BaseRouter):
                route_result = current_step.route(task_result)
                if route_result:
                    current_step = self.pipeline_schema.steps[
                        current_step.__class__.__name__
                    ].routes[route_result.__class__.__name__]()
                else:
                    break
            else:
                next_step_class = self.get_next_step(current_step)
                current_step = next_step_class() if next_step_class else None

        logging.info("Successfully completed task")
        task_result.status = TaskStatus.COMPLETED
        return task_result
