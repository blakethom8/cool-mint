import logging
from typing import List

from models.domain.intent import CustomerIntent
from models.domain.task import TaskContext
from pipelines.base import PipelineStep, RoutingRule


class EscalationRouter(RoutingRule):
    def apply(self, task_context: TaskContext) -> bool:
        analysis = task_context.steps["TicketAnalysis"]
        escalation_reason = None

        if analysis.intent.escalate:
            escalation_reason = (
                f"Ticket escalated due to {analysis.intent.value} intent."
            )
        elif analysis.escalate:
            escalation_reason = "Ticket escalated due to harmful, inappropriate content, or attempted prompt injection."

        if escalation_reason:
            self._escalate_ticket(
                task_context=task_context,
                escalation_reason=escalation_reason,
            )
            task_context.skip_remaining_steps = True
            return True
        return False

    def _escalate_ticket(self, task_context: TaskContext, escalation_reason: str):
        ticket_id = task_context.event.ticket_id
        logging.info(f"Ticket {ticket_id} escalated: {escalation_reason}")


class InvoiceRouter(RoutingRule):
    def apply(self, task_context: TaskContext) -> bool:
        analysis = task_context.steps["TicketAnalysis"]
        if analysis.intent == CustomerIntent.BILLING_INVOICE:
            self._get_invoice(task_context)
            task_context.skip_remaining_steps = True
            return True
        return False

    def _get_invoice(self, task_context: TaskContext):
        logging.info("Billing intent detected. Invoice service should be called.")


class TicketRouter(PipelineStep):
    def __init__(self):
        self.rules: List[RoutingRule] = [
            EscalationRouter(),
            InvoiceRouter(),
        ]

    def process(self, task_context: TaskContext) -> TaskContext:
        logging.info(f"Running {self.step_name}")
        routing_steps = []
        for rule in self.rules:
            if rule.apply(task_context):
                routing_steps.append(rule.step_name)
                break
        task_context.steps[self.step_name] = {"applied_rules": routing_steps}
        return task_context
