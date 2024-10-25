import logging
from typing import Dict, Type
from api.event_schema import EventSchema
from core.pipeline import Pipeline
from pipelines.customer_pipeline import CustomerSupportPipeline
from pipelines.internal_pipeline import InternalHelpdeskPipeline


class PipelineRegistry:
    """
    Implement your logic to determine the pipeline type based on the event.
    We're currently using the email address to determine the pipeline type.
    The options are "support" (CustomerSupportPipeline) and "helpdesk" (InternalHelpdeskPipeline)
    """

    pipelines: Dict[str, Type[Pipeline]] = {
        "support": CustomerSupportPipeline,
        "helpdesk": InternalHelpdeskPipeline,
    }

    @staticmethod
    def get_pipeline_type(event: EventSchema) -> str:
        return event.to_email.split("@")[0]

    @staticmethod
    def get_pipeline(event: EventSchema) -> Pipeline:
        pipeline_type = PipelineRegistry.get_pipeline_type(event)
        pipeline = PipelineRegistry.pipelines.get(pipeline_type)
        if pipeline:
            logging.info(f"Using pipeline: {pipeline.__name__}")
            return pipeline()
        raise ValueError(f"Unknown pipeline type: {pipeline_type}")
