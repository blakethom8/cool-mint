import sys

sys.path.append("..")

from utils.event_factory import EventFactory
from pipelines.registry import PipelineRegistry


event = EventFactory.create_event(event_key="invoice")
pipeline = PipelineRegistry.get_pipeline(event)
result = pipeline.run(event)
