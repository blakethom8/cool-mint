from enum import Enum
from typing import Dict, Type

from workflows.langfuse_tracing_workflow import LangfuseTracingWorkflow
from workflows.market_data_explorer_workflow import MarketDataExplorerWorkflow
from workflows.monthly_activity_summary_workflow import (
    MonthlyActivitySummaryWorkflow,
)
from workflows.forward_email_parsing_workflow import ForwardEmailParsingWorkflow


class WorkflowRegistry(Enum):
    LANGFUSE_TRACING = LangfuseTracingWorkflow
    MARKET_DATA_EXPLORER = MarketDataExplorerWorkflow
    MONTHLY_ACTIVITY_SUMMARY = MonthlyActivitySummaryWorkflow
    FORWARD_EMAIL_PARSING = ForwardEmailParsingWorkflow
