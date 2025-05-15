from core.schema import WorkflowSchema, NodeConfig
from core.workflow import Workflow
from schemas.langfuse_tracing_schema import LangfuseTracingEventSchema
from workflows.langfuse_tracing_workflow_nodes.context_summary_result_node import ContextSummaryResult
from workflows.langfuse_tracing_workflow_nodes.remove_comment_node import RemoveCommentNode
from workflows.langfuse_tracing_workflow_nodes.violation_detection_node import ViolationDetectionNode


class LangfuseTracingWorkflow(Workflow):
    workflow_schema = WorkflowSchema(
        description="",
        event_schema=LangfuseTracingEventSchema,
        start=ViolationDetectionNode,
        nodes=[
            NodeConfig(
                node=ViolationDetectionNode,
                connections=[ContextSummaryResult],
                description="",
                parallel_nodes=[],
            ),
            NodeConfig(
                node=ContextSummaryResult,
                connections=[RemoveCommentNode],
                description="",
                parallel_nodes=[],
            ),
            NodeConfig(
                node=RemoveCommentNode,
                connections=[],
                description="",
                parallel_nodes=[],
            )
        ],
    )
    