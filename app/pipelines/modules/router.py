from abc import ABC, abstractmethod
from typing import Optional

from pipelines.core.task import TaskContext
from pipelines.core.base import BaseStep


class BaseRouter(BaseStep):
    def process(self, task_context: TaskContext) -> TaskContext:
        next_step = self.route(task_context)
        task_context.steps[self.step_name] = {"next_step": next_step.step_name}
        return task_context

    def route(self, task_context: TaskContext) -> BaseStep:
        for route_step in self.routes:
            next_step = route_step.determine_next_step(task_context)
            if next_step:
                return next_step
        return self.fallback if self.fallback else None


class RouterStep(ABC):
    @abstractmethod
    def determine_next_step(self, task_context: TaskContext) -> Optional[BaseStep]:
        pass

    @property
    def step_name(self):
        return self.__class__.__name__
