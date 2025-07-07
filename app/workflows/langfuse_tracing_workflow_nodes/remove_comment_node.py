import logging

from app.core.nodes.base import Node
from app.core.task import TaskContext
from app.schemas.langfuse_tracing_schema import LangfuseTracingEventSchema
from app.workflows.langfuse_tracing_workflow_nodes.violation_detection_node import (
    ViolationDetectionNode,
)


class RemoveCommentNode(Node):
    def remove_comment(self, comment_id: str) -> str:
        result = f"Removed comment with ID: {comment_id}"
        logging.info(result)
        return result

    def process(self, task_context: TaskContext) -> TaskContext:
        violation_result: ViolationDetectionNode.ViolationDetectionResult = (
            task_context.nodes[ViolationDetectionNode.__name__]["results"]
        )

        if violation_result.violation:
            event: LangfuseTracingEventSchema = task_context.event
            result = self.remove_comment(event.comment_id)
        else:
            result = "No violation detected, skipping comment removal."
            logging.info(result)

        task_context.update_node(node_name=self.node_name, results=result)

        return task_context
