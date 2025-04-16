from core.base import Node
from core.task import TaskContext
from pipelines.utils import PipelineUtils


class DefaultNode(Node):
    def process(self, task_context: TaskContext) -> TaskContext:
        event = PipelineUtils.get_default_event_schema(task_context)
        print(event)
        return task_context
