import logging
from typing import Dict, Type
from api.schemas.event import EventSchema
from pipelines.core.pipeline import BasePipeline
from pipelines.customer import CustomerPipeline
# from pipelines.internal.internal_pipeline import InternalPipeline


class PipelineRegistry:
    pipelines: Dict[str, Type[BasePipeline]] = {
        "support": CustomerPipeline,
        # "helpdesk": InternalPipeline,
    }

    """
    Implement your logic to determine the pipeline type based on the event.
    """

    @staticmethod
    def get_pipeline_type(event: EventSchema) -> str:
        return event.to_email.split("@")[0]

    @staticmethod
    def get_pipeline(event: EventSchema) -> BasePipeline:
        pipeline_type = PipelineRegistry.get_pipeline_type(event)
        pipeline = PipelineRegistry.pipelines.get(pipeline_type)
        if pipeline:
            logging.info(f"Using pipeline: {pipeline.__name__}")
            return pipeline()
        raise ValueError(f"Unknown pipeline type: {pipeline_type}")
