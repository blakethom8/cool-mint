import logging
from abc import ABC, abstractmethod
from typing import List

from api.schemas.event import EventSchema
from models.domain.task import TaskStatus, TaskContext


class RoutingRule(ABC):
    @abstractmethod
    def apply(self, task_context: TaskContext) -> bool:
        pass

    @property
    def step_name(self):
        return self.__class__.__name__


class PipelineStep(ABC):
    @abstractmethod
    def process(self, task_result: TaskContext) -> TaskContext:
        pass

    @property
    def step_name(self):
        return self.__class__.__name__


class BasePipeline(ABC):
    def __init__(self):
        self.steps: List[PipelineStep] = []

    def add_step(self, step: PipelineStep):
        self.steps.append(step)

    def run(self, event: EventSchema) -> TaskContext:
        task_result = TaskContext(event=event)
        task_result.status = TaskStatus.RUNNING
        for step in self.steps:
            task_result = step.process(task_result)
            if task_result.skip_remaining_steps:
                break
        logging.info("Successfully completed task")
        task_result.status = TaskStatus.COMPLETED
        return task_result
