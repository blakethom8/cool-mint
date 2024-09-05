import logging
from typing import List

from models.domain.intent import InternalIntent
from models.domain.task import TaskContext
from pipelines.base import PipelineStep, RoutingRule


class AppointmentRouter(RoutingRule):
    def apply(self, task_context: TaskContext) -> bool:
        analysis = task_context.steps["TicketAnalysis"]
        if analysis.intent == InternalIntent.IT_SUPPORT:
            self._get_invoice(task_context)
            task_context.skip_remaining_steps = True
            return True
        return False

    def _get_invoice(self, task_context: TaskContext):
        logging.info(
            "IT Support intent detected. Appointment service should be called."
        )


class TicketRouter(PipelineStep):
    def __init__(self):
        self.rules: List[RoutingRule] = [
            AppointmentRouter(),
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
