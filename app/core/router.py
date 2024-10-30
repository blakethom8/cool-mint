from abc import ABC, abstractmethod
from typing import Optional

from core.task import TaskContext
from core.base import Node


class BaseRouter(Node):
    def process(self, task_context: TaskContext) -> TaskContext:
        next_node = self.route(task_context)
        task_context.nodes[self.node_name] = {"next_node": next_node.node_name}
        return task_context

    def route(self, task_context: TaskContext) -> Node:
        for route_node in self.routes:
            next_node = route_node.determine_next_node(task_context)
            if next_node:
                return next_node
        return self.fallback if self.fallback else None


class RouterNode(ABC):
    @abstractmethod
    def determine_next_node(self, task_context: TaskContext) -> Optional[Node]:
        pass

    @property
    def node_name(self):
        return self.__class__.__name__
