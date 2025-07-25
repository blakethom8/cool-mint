import logging

from core.nodes.base import Node
from core.task import TaskContext
from schemas.nylas_email_schema import EmailObject
from services.nylas_service import NylasService


class HandleSpamNode(Node):
    def process(self, task_context: TaskContext) -> TaskContext:
        logging.info("Handling spam")

        nylas_service = NylasService()
        email_object = EmailObject(**task_context.event.data["object"])

        nylas_service.delete_email(email_object)

        return task_context
