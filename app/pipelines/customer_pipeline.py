from core.pipeline import Pipeline
from core.schema import PipelineSchema, StepConfig
from pipelines.customer.analyze_ticket import AnalyzeTicket
from pipelines.customer.escalate_ticket import EscalateTicket
from pipelines.customer.process_invoice import ProcessInvoice
from pipelines.customer.route_ticket import TicketRouter
from pipelines.customer.generate_response import GenerateResponse
from pipelines.customer.send_reply import SendReply


class CustomerSupportPipeline(Pipeline):
    pipeline_schema = PipelineSchema(
        description="Pipeline for handling customer support tickets based on support@ email",
        start=AnalyzeTicket,
        nodes=[
            StepConfig(
                node=AnalyzeTicket,
                connections=[TicketRouter],
                description="Analyze the incoming customer ticket",
            ),
            StepConfig(
                node=TicketRouter,
                connections=[EscalateTicket, ProcessInvoice, GenerateResponse],
                is_router=True,
                description="Route the ticket based on analysis",
            ),
            StepConfig(
                node=EscalateTicket,
                description="Escalate the ticket to a human agent",
            ),
            StepConfig(
                node=ProcessInvoice,
                description="Process any invoice-related requests",
            ),
            StepConfig(
                node=GenerateResponse,
                connections=[SendReply],
                description="Generate an automated response",
            ),
            StepConfig(
                node=SendReply,
                description="Send the reply to the customer",
            ),
        ],
    )
