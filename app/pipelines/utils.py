from api.event_schema import DefaultEventSchema
from core.task import TaskContext


class PipelineUtils:
    @staticmethod
    def get_default_event_schema(task_context: TaskContext) -> DefaultEventSchema:
        return DefaultEventSchema(**task_context.event)
