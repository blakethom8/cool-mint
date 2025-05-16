import sys
from pathlib import Path

from workflows.langfuse_tracing_workflow import LangfuseTracingWorkflow

project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / "app"))
sys.path.append(str(project_root))

from core.workflow import Workflow
from playground.utils.visualize_workflow import visualize_workflow

"""
This playground is used to visualize the workflows.
"""


def generate(workflow: Workflow):
    image = visualize_workflow(workflow)
    with open("workflow.png", "wb") as f:
        f.write(image.data)


generate(LangfuseTracingWorkflow())
