import logging
from abc import ABC, abstractmethod
from typing import List, Type
from contextlib import contextmanager

from api.schemas.event import EventSchema
from pipelines.core.task import TaskContext, TaskStatus


class RoutingRule(ABC):
    @abstractmethod
    def apply(self, task_context: TaskContext) -> bool:
        pass

    @property
    def step_name(self):
        return self.__class__.__name__


class BaseStep(ABC):
    @property
    def step_name(self):
        return self.__class__.__name__

    @abstractmethod
    def process(self, task_result: TaskContext) -> TaskContext:
        pass


class RouterStep(BaseStep):
    @abstractmethod
    def apply(self, task_context: TaskContext) -> bool:
        pass


class BasePipeline(ABC):
    steps: List[Type[BaseStep]] = []

    @contextmanager
    def step_context(self, step_name: str):
        logging.info(f"Starting step: {step_name}")
        try:
            yield
        except Exception as e:
            logging.error(f"Error in step {step_name}: {str(e)}")
            raise
        finally:
            logging.info(f"Finished step: {step_name}")

    def run(self, event: EventSchema) -> TaskContext:
        task_result = TaskContext(event=event, status=TaskStatus.RUNNING)
        for step in self.steps:
            with self.step_context(step.step_name):
                task_result = step.process(task_result)
                if task_result.skip_remaining_steps:
                    break
        logging.info("Successfully completed task")
        task_result.status = TaskStatus.COMPLETED
        return task_result
