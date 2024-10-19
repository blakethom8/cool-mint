from abc import ABC, abstractmethod

from core.task import TaskContext


class Step(ABC):
    @property
    def step_name(self):
        return self.__class__.__name__

    @abstractmethod
    def process(self, task_result: TaskContext) -> TaskContext:
        pass
