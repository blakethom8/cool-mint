from enum import Enum

from workflows.email_workflow import EmailWorkflow
from workflows.market_exploration_workflow import MarketExplorationWorkflow


class WorkflowRegistry(Enum):
    EMAIL = EmailWorkflow
    MARKET_EXPLORATION = MarketExplorationWorkflow
