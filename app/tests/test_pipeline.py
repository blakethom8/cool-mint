from unittest.mock import patch

from api.schemas.event import EventSchema
from models.domain.intent import CustomerIntent
from models.domain.task import TaskContext
from pipelines.customer.steps.customer_ticket_analysis import (
    TicketAnalysis,
    AnalysisResponseModel,
)
from pipelines.registry import PipelineRegistry
from utils.event_factory import EventFactory


class TestCustomerPipeline:
    def __run_pipeline(self, event: EventSchema) -> TaskContext:
        pipeline = PipelineRegistry.get_pipeline(event)
        return pipeline.run(event)

    def test_invoice_inquiry(self):
        event = EventFactory.create_event(event_key="invoice")

        with patch.object(TicketAnalysis, "analyze_input") as mock_analyze_input:
            mock_analyze_input.return_value = AnalysisResponseModel(
                reasoning="Customer asks for an invoice.",
                intent=CustomerIntent.BILLING_INVOICE.value,
                confidence=1,
                escalate=False,
            )

            task_context = self.__run_pipeline(event)

            assert (
                task_context.steps["TicketAnalysis"].reasoning
                == mock_analyze_input.return_value.reasoning
            )
            assert (
                task_context.steps["TicketAnalysis"].intent
                == mock_analyze_input.return_value.intent
            )
            assert (
                task_context.steps["TicketAnalysis"].confidence
                == mock_analyze_input.return_value.confidence
            )
            assert (
                task_context.steps["TicketAnalysis"].escalate
                == mock_analyze_input.return_value.escalate
            )
            assert task_context.status == "completed"
