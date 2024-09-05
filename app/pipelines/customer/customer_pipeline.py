from pipelines.base import BasePipeline
from pipelines.customer.steps.customer_ticket_analysis import TicketAnalysis
from pipelines.customer.steps.customer_ticket_router import TicketRouter
from pipelines.customer.steps.customer_ticket_response import TicketResponse
from pipelines.customer.steps.customer_ticket_update import TicketUpdate


class CustomerPipeline(BasePipeline):
    def __init__(self):
        super().__init__()
        self.add_step(TicketAnalysis())
        self.add_step(TicketRouter())
        self.add_step(TicketResponse())
        self.add_step(TicketUpdate())
