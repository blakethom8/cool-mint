from pipelines.core.pipeline import Pipeline, PipelineSchema, StepConfig
from pipelines.customer.steps.analyze_ticket import AnalyzeTicket
from pipelines.customer.steps.route_ticket import TicketRouter
from pipelines.customer.steps.generate_response import GenerateResponse
from pipelines.common.send_reply import UpdateTicket
from utils.visualize_pipeline import visualize_pipeline
from decorators.validate_pipeline import validate_pipeline


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
                "GenerateResponse": StepConfig(next=UpdateTicket),
                "UpdateTicket": StepConfig(end=True),
            },
        )
        self.initialize_steps()


if __name__ == "__main__":
    pipeline = InternalPipeline()
    visualize_pipeline(pipeline)
