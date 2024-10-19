from typing import Optional

from pipelines.customer.analyze_ticket import CustomerIntent
from core.task import TaskContext
from core.base import Step
from core.router import BaseRouter, RouterStep
from pipelines.customer.escalate_ticket import EscalateTicket
from pipelines.customer.process_invoice import ProcessInvoice
from pipelines.customer.generate_response import GenerateResponse


class TicketRouter(BaseRouter):
    def __init__(self):
        self.routes = [
            EscalationRouter(),
            InvoiceRouter(),
        ]
        self.fallback = GenerateResponse()


class EscalationRouter(RouterStep):
    def determine_next_step(self, task_context: TaskContext) -> Optional[Step]:
        analysis = task_context.steps["AnalyzeTicket"]
        if analysis.intent.escalate or analysis.escalate:
            return EscalateTicket()
        return None


class InvoiceRouter(RouterStep):
    def determine_next_step(self, task_context: TaskContext) -> Optional[Step]:
        analysis = task_context.steps["AnalyzeTicket"]
        if analysis.intent == CustomerIntent.BILLING_INVOICE:
            return ProcessInvoice()
        return None
