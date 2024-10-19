from pipelines.core.pipeline import BasePipeline, PipelineSchema, StepConfig
from pipelines.steps.analyze_ticket import AnalyzeTicket
from pipelines.steps.escalate_ticket import EscalateTicket
from pipelines.steps.process_invoice import ProcessInvoice
from pipelines.steps.route_ticket import TicketRouter
from pipelines.steps.generate_response import GenerateResponse
from pipelines.steps.update_ticket import UpdateTicket
from utils.visualize_pipeline import visualize_pipeline
from decorators.validate_pipeline import validate_pipeline


@validate_pipeline
class CustomerPipeline(BasePipeline):
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
                "EscalateTicket": StepConfig(next=None),
                "ProcessInvoice": StepConfig(next=None),
                "GenerateResponse": StepConfig(next=UpdateTicket),
                "UpdateTicket": StepConfig(next=None),
            },
        )
        self.initialize_steps()


if __name__ == "__main__":
    pipeline = CustomerPipeline()
    visualize_pipeline(pipeline)
