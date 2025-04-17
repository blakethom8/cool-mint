from api.event_schema import DefaultEventSchema
from core.workflow import Workflow
from core.schema import WorkflowSchema, NodeConfig
from workflows.default_workflow_nodes.default_node import DefaultNode


class DefaultWorkflow(Workflow):
    workflow_schema = WorkflowSchema(
        description="Empty default workflow",
        event_schema=DefaultEventSchema,
        start=DefaultNode,
        nodes=[
            NodeConfig(
                node=DefaultNode,
                connections=[],
                description="Empty default node",
            ),
        ],
    )
