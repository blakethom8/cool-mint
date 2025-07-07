from enum import Enum
from typing import Dict, Type

from app.workflows.langfuse_tracing_workflow import LangfuseTracingWorkflow
from app.workflows.market_data_explorer_workflow import MarketDataExplorerWorkflow
from app.workflows.monthly_activity_summary_workflow import (
    MonthlyActivitySummaryWorkflow,
)


class WorkflowRegistry(Enum):
    LANGFUSE_TRACING = LangfuseTracingWorkflow
    MARKET_DATA_EXPLORER = MarketDataExplorerWorkflow
    MONTHLY_ACTIVITY_SUMMARY = MonthlyActivitySummaryWorkflow
