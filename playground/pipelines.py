import sys

sys.path.append("..")

from utils.event_factory import EventFactory
from pipelines.registry import PipelineRegistry

event = EventFactory.create_event(event_key="invoice")
pipeline = PipelineRegistry.get_pipeline(event)
output = pipeline.run(event)

event = EventFactory.create_event(event_key="product")
pipeline = PipelineRegistry.get_pipeline(event)
output = pipeline.run(event)

event = EventFactory.create_event(event_key="policy_question")
pipeline = PipelineRegistry.get_pipeline(event)
output = pipeline.run(event)

output.model_dump()

print(output.result.reasoning)
print(output.result.response)
