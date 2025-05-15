from enum import Enum

from workflows.langfuse_tracing_workflow import LangfuseTracingWorkflow


class WorkflowRegistry(Enum):
    LANGFUSE_TRACING = LangfuseTracingWorkflow
