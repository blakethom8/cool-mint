from core.pipeline import Pipeline
from core.schema import PipelineSchema, StepConfig
from pipelines.internal.analyze_ticket import AnalyzeTicket
from pipelines.internal.route_ticket import TicketRouter
from pipelines.internal.generate_response import GenerateResponse
from pipelines.internal.get_appointments import GetAppointment
from pipelines.customer.send_reply import SendReply


class InternalPipeline(Pipeline):
    pipeline_schema = PipelineSchema(
        start="AnalyzeTicket",
        steps={
            "AnalyzeTicket": StepConfig(step=AnalyzeTicket, next=["TicketRouter"]),
            "TicketRouter": StepConfig(
                step=TicketRouter,
                next=["GenerateResponse", "GetAppointment"],
                is_router=True,
            ),
            "GenerateResponse": StepConfig(step=GenerateResponse, next=["SendReply"]),
            "GetAppointment": StepConfig(step=GetAppointment),
            "SendReply": StepConfig(step=SendReply),
        },
    )
