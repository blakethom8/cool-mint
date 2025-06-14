"""
Market Data Explorer Workflow

This workflow processes user queries about market data,
determining if additional search is needed.
"""

from typing import Dict, Any

from app.core.schema import WorkflowSchema, NodeConfig
from app.core.workflow import Workflow
from app.core.task import TaskContext

from app.workflows.market_data_explorer_nodes.search_classifier import (
    SearchClassifierNode,
)
from app.schemas.market_data_explorer_schema import MarketDataExplorerEvent


class MarketDataExplorerWorkflow(Workflow):
    """Workflow for market data exploration."""

    workflow_schema = WorkflowSchema(
        description="Analyzes user queries to determine if additional market data search is needed",
        event_schema=MarketDataExplorerEvent,  # Using our custom event schema
        start=SearchClassifierNode,
        nodes=[
            NodeConfig(
                node=SearchClassifierNode,
                connections=[],  # No downstream connections for now
                description="Determines if a search is needed for the user query",
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
            Dictionary containing the classification results
        """
        workflow = MarketDataExplorerWorkflow()
        result = workflow.run(event_data)

        return {
            "success": True,
            "query": event_data.get("query", ""),
            "needs_search": result.data.get("needs_search", False),
            "reason": result.data.get("reason", ""),
            "metadata": result.metadata,
            "user_id": event_data.get("user_id", "anonymous"),
            "session_id": event_data.get("session_id", ""),
        }
