"""
Market Data Explorer Workflow

This workflow processes user queries about market data,
determining if additional search is needed and identifying potential targets.
"""

from typing import Dict, Any

from core.schema import WorkflowSchema, NodeConfig
from core.workflow import Workflow
from core.task import TaskContext

from workflows.market_data_explorer_nodes.search_classifier import (
    SearchClassifierNode,
)
from workflows.market_data_explorer_nodes.target_identify_node import (
    TargetIdentifyNode,
)
from schemas.market_data_explorer_schema import MarketDataExplorerEvent


class MarketDataExplorerWorkflow(Workflow):
    """Workflow for market data exploration."""

    workflow_schema = WorkflowSchema(
        description="Analyzes user queries and market data for insights",
        event_schema=MarketDataExplorerEvent,
        start=SearchClassifierNode,
        nodes=[
            NodeConfig(
                node=SearchClassifierNode,
                connections=[TargetIdentifyNode],
                description="Determines if a search is needed for the user query",
            ),
            NodeConfig(
                node=TargetIdentifyNode,
                connections=[],
                description="Identifies potential referral targets from market data",
            ),
        ],
    )

    @staticmethod
    def process(event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a market data exploration query.

        Args:
            event_data: Dictionary containing the MarketDataExplorerEvent data

        Returns:
            Dictionary containing the workflow results
        """
        workflow = MarketDataExplorerWorkflow()
        result = workflow.run(event_data)

        return {
            "success": True,
            "query": event_data.get("query", ""),
            "needs_search": result.data.get("needs_search", False),
            "reason": result.data.get("reason", ""),
            "target_identification": result.data.get("target_identification", {}),
            "metadata": result.metadata,
            "user_id": event_data.get("user_id", "anonymous"),
            "session_id": event_data.get("session_id", ""),
        }
