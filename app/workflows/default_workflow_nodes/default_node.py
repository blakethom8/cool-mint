from core.nodes.base import Node
from core.task import TaskContext


class DefaultNode(Node):
    def process(self, task_context: TaskContext) -> TaskContext:
        return task_context
