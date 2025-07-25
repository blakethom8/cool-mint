from core.schema import WorkflowSchema, NodeConfig
from core.workflow import Workflow

from schemas.nylas_webhook_schema import WebhookEvent
from workflows.email_workflow_nodes.email_filter_node import EmailFilterNode
from workflows.email_workflow_nodes.classification_node import ClassificationNode
from workflows.email_workflow_nodes.email_router_node import EmailRouterNode
from workflows.email_workflow_nodes.handle_spam_node import HandleSpamNode
from workflows.email_workflow_nodes.process_invoice_node import ProcessInvoiceNode
from workflows.email_workflow_nodes.send_message_node import SendMessageNode
from workflows.email_workflow_nodes.handle_genai_accelerator import (
    HandleGenAIAcceleratorNode,
)
from typing import Dict, Any


class EmailWorkflow(Workflow):
    workflow_schema = WorkflowSchema(
        description="",
        event_schema=WebhookEvent,
        start=EmailFilterNode,
        nodes=[
            NodeConfig(
                node=EmailFilterNode,
                connections=[ClassificationNode],
                description="",
            ),
            NodeConfig(
                node=ClassificationNode,
                connections=[EmailRouterNode],
                description="",
            ),
            NodeConfig(
                node=EmailRouterNode,
                connections=[
                    HandleSpamNode,
                    ProcessInvoiceNode,
                    SendMessageNode,
                    HandleGenAIAcceleratorNode,
                ],
                description="",
                is_router=True,
            ),
        ],
    )

    @staticmethod
    def process(event_data: Dict[str, Any]) -> None:
        """
        Process an email event.

        Args:
            event_data: The event data to process
        """
        # Implement your email processing logic here
        pass
