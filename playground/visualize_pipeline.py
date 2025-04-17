import sys
from pathlib import Path

from core.workflow import Workflow
from playground.utils.visualize_workflow import visualize_workflow
from workflows.default_workflow import DefaultWorkflow

project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / "app"))

"""
This playground is used to visualize the workflows.
"""


def generate(workflow: Workflow):
    image = visualize_workflow(workflow)
    with open("workflow.png", "wb") as f:
        f.write(image.data)


generate(DefaultWorkflow())
