from core.pipeline import Pipeline, PipelineSchema, StepConfig
from pipelines.customer.analyze_ticket import AnalyzeTicket
from pipelines.customer.escalate_ticket import EscalateTicket
from pipelines.customer.process_invoice import ProcessInvoice
from pipelines.customer.route_ticket import TicketRouter
from pipelines.customer.generate_response import GenerateResponse
from pipelines.customer.send_reply import SendReply
from utils.validate_pipeline import validate_pipeline


@validate_pipeline
class CustomerPipeline(Pipeline):
    def __init__(self):
        super().__init__()
        self.pipeline_schema = PipelineSchema(
            start=AnalyzeTicket,
            steps={
                "AnalyzeTicket": StepConfig(next=TicketRouter),
                "TicketRouter": StepConfig(
                    routes={
                        "EscalateTicket": EscalateTicket,
                        "ProcessInvoice": ProcessInvoice,
                        "GenerateResponse": GenerateResponse,
                    }
                ),
                "EscalateTicket": StepConfig(end=True),
                "ProcessInvoice": StepConfig(end=True),
                "GenerateResponse": StepConfig(next=SendReply),
                "SendReply": StepConfig(end=True),
            },
        )
        self.initialize_steps()
