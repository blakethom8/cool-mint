from abc import abstractmethod, ABC
from pydantic import BaseModel
from pydantic_ai import Agent
from typing import Type

from core.nodes.base import Node
from core.task import TaskContext


class AgentConfig(BaseModel):
    model: str
    system_prompt: str
    deps_type: Type[BaseModel]
    output_type: Type[BaseModel]


class AgentNode(Node, ABC):
    def __init__(self):
        agent_config = self.get_agent_config()
        self.agent = Agent(
            model=agent_config.model,
            system_prompt=agent_config.system_prompt,
            deps_type=agent_config.deps_type,
            output_type=agent_config.output_type,
        )

    @abstractmethod
    def get_agent_config(self) -> AgentConfig:
        pass

    @abstractmethod
    def process(self, task_context: TaskContext) -> TaskContext:
        pass
