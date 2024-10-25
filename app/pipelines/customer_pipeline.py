from core.pipeline import Pipeline
from core.schema import PipelineSchema, StepConfig
from pipelines.customer.analyze_ticket import AnalyzeTicket
from pipelines.customer.escalate_ticket import EscalateTicket
from pipelines.customer.process_invoice import ProcessInvoice
from pipelines.customer.route_ticket import TicketRouter
from pipelines.customer.generate_response import GenerateResponse
from pipelines.customer.send_reply import SendReply


class CustomerPipeline(Pipeline):
    pipeline_schema = PipelineSchema(
        start="AnalyzeTicket",
        steps={
            "AnalyzeTicket": StepConfig(step=AnalyzeTicket, next=["TicketRouter"]),
            "TicketRouter": StepConfig(
                step=TicketRouter,
                next=["EscalateTicket", "ProcessInvoice", "GenerateResponse"],
                is_router=True,
            ),
            "EscalateTicket": StepConfig(step=EscalateTicket),
            "ProcessInvoice": StepConfig(step=ProcessInvoice),
            "GenerateResponse": StepConfig(step=GenerateResponse, next=["SendReply"]),
            "SendReply": StepConfig(step=SendReply),
        },
    )
