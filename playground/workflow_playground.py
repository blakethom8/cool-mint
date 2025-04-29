import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / "app"))
sys.path.append(str(project_root))

from playground.utils.event_factory import EventFactory

"""
This playground is used to test the WorkflowRegistry and the workflows themselves.
"""

# --------------------------------------------------------------
# Test invoice event (customer workflow)
# --------------------------------------------------------------

event = EventFactory.create_event(event_key="default_event")
# workflow = WorkflowRegistry().get_workflow(WorkflowRegistry.PLACEHOLDER.value)
# output = workflow.run(event)
# output.model_dump()
