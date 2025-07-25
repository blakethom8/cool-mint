import logging
from core.nodes.base import Node
from core.task import TaskContext
from schemas.nylas_email_schema import EmailObject
from services.nylas_service import NylasService


class ProcessInvoiceNode(Node):
    def process(self, task_context: TaskContext) -> TaskContext:
        logging.info("Processing invoice")

        email_object = EmailObject(**task_context.event.data["object"])

        if not email_object.attachments:
            error_msg = "No attachments found in the email"
            logging.error(error_msg)
            task_context.update_node(
                node_name=self.__class__.__name__,
                result={"error": error_msg, "success": False},
            )
            task_context.stop_workflow(reason=error_msg)
            return task_context

        try:
            nylas_service = NylasService()
            file_content = nylas_service.download_attachment(
                email=email_object, download=True
            )

            logging.info(
                f"Successfully downloaded attachment: {file_content['filename']}"
            )
            task_context.update_node(
                node_name=self.__class__.__name__,
                result={"file_content": file_content, "success": True},
            )

        except Exception as e:
            error_msg = f"Error downloading attachment: {str(e)}"
            logging.error(error_msg)
            task_context.update_node(
                node_name=self.__class__.__name__,
                result={"error": error_msg, "success": False},
            )
            task_context.stop_workflow(reason=error_msg)

        return task_context
