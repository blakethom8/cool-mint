from pipelines.core.pipeline import Pipeline, PipelineSchema, StepConfig
from pipelines.customer.steps.analyze_ticket import AnalyzeTicket
from pipelines.customer.steps.escalate_ticket import EscalateTicket
from pipelines.customer.steps.process_invoice import ProcessInvoice
from pipelines.customer.steps.route_ticket import TicketRouter
from pipelines.customer.steps.generate_response import GenerateResponse
from pipelines.common.send_reply import SendReply
from decorators.validate_pipeline import validate_pipeline


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
