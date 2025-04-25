from enum import Enum

from workflows.placeholder_workflow import PlaceholderWorkflow


class WorkflowRegistry(Enum):
    PLACEHOLDER = PlaceholderWorkflow
