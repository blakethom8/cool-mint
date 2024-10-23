import os

# Set database host to localhost since we're connecting to it outside of docker
os.environ["DATABASE_HOST"] = "localhost"

from utils.event_factory import EventFactory
from pipelines.registry import PipelineRegistry

# --------------------------------------------------------------
# Test invoice event (customer pipeline)
# --------------------------------------------------------------

event = EventFactory.create_event(event_key="invoice")
pipeline = PipelineRegistry.get_pipeline(event)
output = pipeline.run(event)
output.model_dump()

# --------------------------------------------------------------
# Test product event (customer pipeline + RAG)
# --------------------------------------------------------------

event = EventFactory.create_event(event_key="product")
pipeline = PipelineRegistry.get_pipeline(event)
output = pipeline.run(event)
output.model_dump()

# --------------------------------------------------------------
# Test policy question event (internal pipeline)
# --------------------------------------------------------------

event = EventFactory.create_event(event_key="policy_question")
pipeline = PipelineRegistry.get_pipeline(event)
output = pipeline.run(event)
output.model_dump()
