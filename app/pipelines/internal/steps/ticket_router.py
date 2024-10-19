from typing import Optional

from models.intent import InternalIntent
from pipelines.core.task import TaskContext
from pipelines.core.base import Step
from pipelines.core.router import BaseRouter, RouterStep
from pipelines.internal.steps.get_appointments import GetAppointment
from pipelines.internal.steps.generate_response import GenerateResponse


class TicketRouter(BaseRouter):
    """Router for internal tickets."""

    def __init__(self):
        """Initialize the TicketRouter with routes and fallback."""
        self.routes = [
            AppointmentRouter(),
        ]
        self.fallback = GenerateResponse()


class AppointmentRouter(RouterStep):
    """Router for handling IT support appointments."""

    def determine_next_step(self, task_context: TaskContext) -> Optional[Step]:
        analysis = task_context.steps["AnalyzeTicket"]
        if analysis.intent == InternalIntent.IT_SUPPORT:
            return GetAppointment()
        return None
