from core.pipeline import Pipeline, PipelineSchema, StepConfig
from pipelines.internal.analyze_ticket import AnalyzeTicket
from pipelines.internal.ticket_router import TicketRouter
from pipelines.internal.generate_response import GenerateResponse
from pipelines.customer.send_reply import SendReply
from utils.validate_pipeline import validate_pipeline


@validate_pipeline
class InternalPipeline(Pipeline):
    def __init__(self):
        super().__init__()
        self.pipeline_schema = PipelineSchema(
            start=AnalyzeTicket,
            steps={
                "AnalyzeTicket": StepConfig(next=TicketRouter),
                "TicketRouter": StepConfig(
                    routes={
                        "GenerateResponse": GenerateResponse,
                    }
                ),
                "GenerateResponse": StepConfig(next=SendReply),
                "SendReply": StepConfig(end=True),
            },
        )
        self.initialize_steps()
