from typing import Optional

from core.nodes.base import Node
from core.nodes.router import BaseRouter, RouterNode
from core.task import TaskContext

from workflows.email_workflow_nodes.handle_spam_node import HandleSpamNode
from workflows.email_workflow_nodes.process_invoice_node import ProcessInvoiceNode
from workflows.email_workflow_nodes.send_message_node import SendMessageNode
from workflows.email_workflow_nodes.handle_genai_accelerator import (
    HandleGenAIAcceleratorNode,
)


class EmailRouterNode(BaseRouter):
    def __init__(self):
        self.routes = [
            EmailRoute(),
        ]


class EmailRoute(RouterNode):
    def determine_next_node(self, task_context: TaskContext) -> Optional[Node]:
        category = task_context.nodes["ClassificationNode"]["result"].output.category
        if category == "spam":
            return HandleSpamNode()
        elif category == "invoice":
            return ProcessInvoiceNode()
        elif category == "general":
            return SendMessageNode()
        elif category == "genai_accelerator":
            return HandleGenAIAcceleratorNode()
        return None
