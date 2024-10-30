from abc import ABC, abstractmethod

from core.task import TaskContext


class Node(ABC):
    @property
    def node_name(self):
        return self.__class__.__name__

    @abstractmethod
    def process(self, task_result: TaskContext) -> TaskContext:
        pass
