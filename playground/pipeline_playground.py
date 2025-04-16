import os
import sys
from pathlib import Path

from pipelines.registry import PipelineRegistry, PipelineType
from playground.utils.event_factory import EventFactory

project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / "app"))

# Set database host to localhost since we're connecting to it outside of docker
os.environ["DATABASE_HOST"] = "localhost"

"""
This playground is used to test the PipelineRegistry and the pipelines themselves.
"""

# --------------------------------------------------------------
# Test invoice event (customer pipeline)
# --------------------------------------------------------------

event = EventFactory.create_event(event_key="default_event")
pipeline = PipelineRegistry().get_pipeline(PipelineType.DEFAULT_PIPELINE.value)
output = pipeline.run(event)
output.model_dump()