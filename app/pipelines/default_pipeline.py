from core.pipeline import Pipeline
from core.schema import PipelineSchema, NodeConfig
from pipelines.default_pipeline_nodes.default_node import DefaultNode


class DefaultPipeline(Pipeline):
    pipeline_schema = PipelineSchema(
        description="Empty default pipeline",
        start=DefaultNode,
        nodes=[
            NodeConfig(
                node=DefaultNode,
                connections=[],
                description="Empty default node",
            ),
        ],
    )
