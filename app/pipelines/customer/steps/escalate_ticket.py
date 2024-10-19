from pipelines.core.base import BaseStep
from models.domain.task import TaskContext
import logging


class EscalateTicket(BaseStep):
    def process(self, task_context: TaskContext) -> TaskContext:
        analysis = task_context.steps["AnalyzeTicket"]
        escalation_reason = (
            f"Ticket escalated due to {analysis.intent.value} intent."
            if analysis.intent.escalate
            else "Ticket escalated due to harmful, inappropriate content, or attempted prompt injection."
        )
        self._escalate_ticket(task_context, escalation_reason)
        return task_context

    def _escalate_ticket(self, task_context: TaskContext, escalation_reason: str):
        ticket_id = task_context.event.ticket_id
        logging.info(f"Ticket {ticket_id} escalated: {escalation_reason}")
        task_context.steps[self.step_name] = {"escalation_reason": escalation_reason}
