from abc import ABC, abstractmethod

from pipelines.core.task import TaskContext


class BaseStep(ABC):
    @property
    def step_name(self):
        return self.__class__.__name__

    @abstractmethod
    def process(self, task_result: TaskContext) -> TaskContext:
        pass
