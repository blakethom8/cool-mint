import logging
from core.nodes.base import Node
from core.task import TaskContext
from schemas.nylas_email_schema import EmailObject
from services.nylas_service import NylasService


BODY = """
Hello there,

We've received your message and will get back to you as soon as possible!
"""


class SendMessageNode(Node):
    def process(self, task_context: TaskContext) -> TaskContext:
        logging.info("Sending message")

        nylas_service = NylasService()
        email_object = EmailObject(**task_context.event.data["object"])

        nylas_service.send_email(
            grant_id=email_object.grant_id,
            to=[email_object.from_[0].email],
            subject=email_object.subject,
            body=BODY,
            reply=True,
            reply_to_message_id=email_object.id,
        )
        return task_context
