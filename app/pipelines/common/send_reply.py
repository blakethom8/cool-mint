import logging
from pipelines.core.base import BaseStep
from models.domain.task import TaskContext


class SendReply(BaseStep):
    def process(self, task_context: TaskContext) -> TaskContext:
        logging.info(f"Sending a reply to {task_context.event.sender}")
        return task_context
