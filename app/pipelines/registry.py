import logging
from enum import Enum
from typing import Dict, Type

from core.pipeline import Pipeline
from pipelines.default_pipeline import DefaultPipeline


class PipelineType(str, Enum):
    """
        Replace and add your own pipeline types.
    """
    DEFAULT_PIPELINE = "default_pipeline"


class PipelineRegistry:
    def __init__(self):
        self.pipelines: Dict[str, Type[Pipeline]] = {
            PipelineType.DEFAULT_PIPELINE.value: DefaultPipeline,
        }

    def get_pipeline(self, pipeline_type: str) -> Pipeline:
        pipeline = self.pipelines.get(pipeline_type)
        if pipeline:
            logging.info(f"Using pipeline: {pipeline.__name__}")
            return pipeline()
        raise ValueError(f"Unknown pipeline type: {pipeline_type}")
