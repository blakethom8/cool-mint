from typing import Optional

from models.domain.intent import InternalIntent
from models.domain.task import TaskContext
from pipelines.core.base import BaseStep
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

    def determine_next_step(self, task_context: TaskContext) -> Optional[BaseStep]:
        analysis = task_context.steps["AnalyzeTicket"]
        if analysis.intent == InternalIntent.IT_SUPPORT:
            return GetAppointment()
        return None
