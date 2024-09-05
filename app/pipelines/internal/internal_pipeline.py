from pipelines.base import BasePipeline
from pipelines.internal.steps.internal_ticket_analysis import TicketAnalysis
from pipelines.internal.steps.internal_ticket_router import TicketRouter
from pipelines.internal.steps.internal_ticket_response import TicketResponse
from pipelines.internal.steps.internal_ticket_update import TicketUpdate


class InternalPipeline(BasePipeline):
    def __init__(self):
        super().__init__()
        self.add_step(TicketAnalysis())
        self.add_step(TicketRouter())
        self.add_step(TicketResponse())
        self.add_step(TicketUpdate())
