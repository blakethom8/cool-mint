from enum import Enum

from workflows.langfuse_tracing_workflow import LangfuseTracingWorkflow
from workflows.market_data_explorer_workflow import MarketDataExplorerWorkflow


class WorkflowRegistry(Enum):
    LANGFUSE_TRACING = LangfuseTracingWorkflow
    MARKET_DATA_EXPLORER = MarketDataExplorerWorkflow
