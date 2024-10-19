import logging
from pipelines.core.base import BaseStep
from models.domain.task import TaskContext


class TicketUpdate(BaseStep):
    def process(self, task_context: TaskContext) -> TaskContext:
        logging.info(f"Running {self.step_name}")
        logging.info(f"Sending a reply to {task_context.event.sender}")
        logging.info(f"Ticket reasoning: {task_context.result.reasoning}")
        return task_context
