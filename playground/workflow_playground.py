import os
import sys
from pathlib import Path

from playground.utils.event_factory import EventFactory

project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / "app"))

# Set database host to localhost since we're connecting to it outside of docker
os.environ["DATABASE_HOST"] = "localhost"

"""
This playground is used to test the WorkflowRegistry and the workflows themselves.
"""

# --------------------------------------------------------------
# Test invoice event (customer workflow)
# --------------------------------------------------------------

event = EventFactory.create_event(event_key="default_event")
# workflow = WorkflowRegistry().get_workflow(WorkflowType.DEFAULT_PIPELINE.value)
# output = workflow.run(event)
# output.model_dump()
