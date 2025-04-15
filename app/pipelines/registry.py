import logging
from enum import Enum
from typing import Dict, Type

from core.pipeline import Pipeline

"""
Pipeline Registry Module

This module provides a registry system for managing different pipeline types
and their mappings. It determines which pipeline to use based on event attributes,
currently using email addresses as the routing mechanism.
"""

class PipelineType(str, Enum):
    pass

class PipelineRegistry:
    def __init__(self):
        self.pipelines: Dict[str, Type[Pipeline]] = {}

    def get_pipeline(self, pipeline_type: PipelineType) -> Pipeline:
        pipeline = self.pipelines.get(pipeline_type)
        if pipeline:
            logging.info(f"Using pipeline: {pipeline.__name__}")
            return pipeline()
        raise ValueError(f"Unknown pipeline type: {pipeline_type}")
