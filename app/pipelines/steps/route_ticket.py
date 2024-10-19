from typing import Optional

from models.domain.intent import CustomerIntent
from models.domain.task import TaskContext
from pipelines.core.base import BaseStep
from pipelines.core.router import BaseRouter, RouterStep
from pipelines.steps.escalate_ticket import EscalateTicket
from pipelines.steps.process_invoice import ProcessInvoice
from pipelines.steps.generate_response import GenerateResponse


class TicketRouter(BaseRouter):
    def __init__(self):
        self.routes = [
            EscalationRouter(),
            InvoiceRouter(),
        ]
        self.fallback = GenerateResponse()


class EscalationRouter(RouterStep):
    def determine_next_step(self, task_context: TaskContext) -> Optional[BaseStep]:
        analysis = task_context.steps["AnalyzeTicket"]
        if analysis.intent.escalate or analysis.escalate:
            return EscalateTicket()
        return None


class InvoiceRouter(RouterStep):
    def determine_next_step(self, task_context: TaskContext) -> Optional[BaseStep]:
        analysis = task_context.steps["AnalyzeTicket"]
        if analysis.intent == CustomerIntent.BILLING_INVOICE:
            return ProcessInvoice()
        return None
