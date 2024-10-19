from typing import Optional

from models.domain.intent import CustomerIntent
from pipelines.core.task import TaskContext
from pipelines.modules.base import BaseStep
from pipelines.modules.router import RouterStep
from pipelines.steps.escalate_ticket import Escalation
from pipelines.steps.process_invoice import Invoice
from pipelines.steps.generate_response import Response


class Router(BaseStep):
    def __init__(self):
        self.routes = [
            EscalationRouter(),
            InvoiceRouter(),
        ]
        self.fallback = Response()

    def process(self, task_context: TaskContext) -> TaskContext:
        next_step = self.route(task_context)
        task_context.steps[self.step_name] = {"next_step": next_step.step_name}
        return task_context

    def route(self, task_context: TaskContext) -> BaseStep:
        for route_step in self.routes:
            next_step = route_step.determine_next_step(task_context)
            if next_step:
                return next_step
        return self.fallback


class EscalationRouter(RouterStep):
    def determine_next_step(self, task_context: TaskContext) -> Optional[BaseStep]:
        analysis = task_context.steps["Analysis"]
        if analysis.intent.escalate or analysis.escalate:
            return Escalation()
        return None


class InvoiceRouter(RouterStep):
    def determine_next_step(self, task_context: TaskContext) -> Optional[BaseStep]:
        analysis = task_context.steps["Analysis"]
        if analysis.intent == CustomerIntent.BILLING_INVOICE:
            return Invoice()
        return None
