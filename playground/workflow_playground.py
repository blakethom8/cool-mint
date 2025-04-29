import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / "app"))
sys.path.append(str(project_root))

from playground.utils.event_loader import EventLoader
from workflows.workflow_registry import WorkflowRegistry

"""
This playground is used to test the WorkflowRegistry and the workflows themselves.
"""

# --------------------------------------------------------------
# Test invoice event (customer workflow)
# --------------------------------------------------------------

event = EventLoader.load_event(event_key="placeholder_event")
workflow = WorkflowRegistry.PLACEHOLDER.value()
output = workflow.run(event)
output.model_dump()
