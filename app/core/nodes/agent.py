from abc import abstractmethod, ABC
from pydantic import BaseModel
from pydantic_ai import Agent

from core.nodes.base import Node
from core.task import TaskContext


class AgentNode(Node, ABC):

    class DepsType(BaseModel):
        pass

    class OutputType(BaseModel):
        pass

    def __init__(self):
        self.agent = self.create_agent()

    @abstractmethod
    def create_agent(self) -> Agent:
        pass

    @abstractmethod
    def process(self, task_context: TaskContext) -> TaskContext:
        pass
