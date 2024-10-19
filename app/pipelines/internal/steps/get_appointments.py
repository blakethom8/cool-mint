import logging
from models.domain.task import TaskContext
from pipelines.core.base import BaseStep


class GetAppointment(BaseStep):
    """Step for getting an IT support appointment."""

    def process(self, task_context: TaskContext) -> TaskContext:
        logging.info(
            "IT Support intent detected. Appointment service should be called."
        )
        return task_context
