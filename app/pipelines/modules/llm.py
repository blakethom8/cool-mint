from abc import ABC, abstractmethod

from pipelines.core.task import TaskContext
from pipelines.core.base import BaseStep
from pydantic import BaseModel


class LLMStep(BaseStep, ABC):
    class ContextModel(BaseModel):
        pass

    class ResponseModel(BaseModel):
        pass

    @abstractmethod
    def create_completion(self, context: ContextModel) -> ResponseModel:
        pass

    @abstractmethod
    def get_context(self, task_context: TaskContext) -> ContextModel:
        pass

    @abstractmethod
    def process(self, task_context: TaskContext) -> TaskContext:
        pass
