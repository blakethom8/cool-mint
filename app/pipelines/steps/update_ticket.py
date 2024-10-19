import logging
from pipelines.core.base import BaseStep
from models.domain.task import TaskContext


class UpdateTicket(BaseStep):
    def process(self, task_context: TaskContext) -> TaskContext:
        logging.info(f"Sending a reply to {task_context.event.sender}")
        logging.info(
            f"Ticket reasoning: {task_context.steps['GenerateResponse'].reasoning}"
        )
        return task_context
