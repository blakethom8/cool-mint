"""
Unified SQL Data Node

This node combines SQL query execution with data structuring using the analyzer pattern.
It replaces the separate SQL and data structure nodes with a single, unified approach.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, date, timedelta

from app.core.nodes.base import Node
from app.core.task import TaskContext
from app.database.session import SessionLocal
from app.workflows.salesforce_data_analyzer.analyzers.base_analyzer import BaseAnalyzer


class UnifiedSQLDataNode(Node):
    """
    Node that executes SQL queries and structures data using the analyzer pattern.

    This node:
    1. Gets the selected analyzer from task context
    2. Executes the analyzer's SQL query
    3. Structures the data using the analyzer's structuring logic
    4. Stores the results in task context
    """

    def __init__(self, debug_mode: bool = False, export_debug_data: bool = False):
        self.debug_mode = debug_mode
        self.export_debug_data = export_debug_data
        self.logger = logging.getLogger(__name__)

    def process(self, task_context: TaskContext) -> TaskContext:
        """
        Execute the analyzer's SQL query and structure the data.

        Args:
            task_context: Task context containing the selected analyzer and event data

        Returns:
            Updated task context with structured data
        """
        try:
            # Get the selected analyzer from task context
            analyzer = self._get_analyzer_from_context(task_context)
            if not analyzer:
                raise ValueError("No analyzer found in task context")

            # Extract parameters from event
            query_params = self._extract_query_parameters(task_context)

            self.logger.info(
                f"Executing {analyzer.analyzer_name} for user {query_params.get('user_id')} "
                f"from {query_params.get('start_date')} to {query_params.get('end_date')}"
            )

            # Get database session
            db_session = SessionLocal()

            try:
                # Execute query and structure data using the analyzer
                structured_data = analyzer.execute_and_structure(
                    db_session, query_params
                )

                # Store results in task context
                task_context.update_node(
                    node_name=self.node_name, result=structured_data
                )
                task_context.metadata["sql_data_retrieved"] = True
                task_context.metadata["analyzer_used"] = analyzer.analyzer_name
                task_context.metadata["raw_record_count"] = structured_data.get(
                    "_metadata", {}
                ).get("raw_record_count", 0)

                # Debug and export if enabled
                if self.debug_mode:
                    self._log_debug_info(structured_data, analyzer)

                if self.export_debug_data:
                    self._export_debug_data(structured_data, task_context, analyzer)

                self.logger.info(
                    f"Successfully executed {analyzer.analyzer_name} and retrieved "
                    f"{structured_data.get('_metadata', {}).get('raw_record_count', 0)} raw records"
                )

                return task_context

            finally:
                db_session.close()

        except Exception as e:
            self.logger.error(f"Error in unified SQL data node: {str(e)}")
            task_context.update_node(
                node_name=self.node_name, error=str(e), result=None
            )
            task_context.metadata["sql_data_retrieved"] = False
            task_context.metadata["error"] = str(e)
            return task_context

    def _get_analyzer_from_context(
        self, task_context: TaskContext
    ) -> Optional[BaseAnalyzer]:
        """
        Get the selected analyzer from task context.

        Args:
            task_context: Task context containing analyzer selection

        Returns:
            Selected analyzer instance or None
        """
        # The analyzer should be set by the request category node
        return task_context.metadata.get("selected_analyzer")

    def _extract_query_parameters(self, task_context: TaskContext) -> Dict[str, Any]:
        """
        Extract query parameters from the task context event.

        Args:
            task_context: Task context containing event data

        Returns:
            Dictionary of query parameters
        """
        event = task_context.event

        # Extract basic parameters
        user_id = getattr(event, "user_id", None)
        start_date = getattr(event, "start_date", None)
        end_date = getattr(event, "end_date", None)

        # If dates are not provided, use default range
        if not start_date or not end_date:
            end_date = date.today()
            start_date = end_date - timedelta(days=30)

        # Create parameter dictionary
        query_params = {
            "user_id": user_id,
            "start_date": start_date,
            "end_date": end_date,
        }

        # Add any additional parameters from the event
        if hasattr(event, "additional_params"):
            query_params.update(event.additional_params)

        return query_params

    def _log_debug_info(
        self, structured_data: Dict[str, Any], analyzer: BaseAnalyzer
    ) -> None:
        """
        Log debug information about the structured data.

        Args:
            structured_data: The structured data result
            analyzer: The analyzer that was used
        """
        metadata = structured_data.get("_metadata", {})

        self.logger.info("=== UNIFIED SQL DATA NODE DEBUG ===")
        self.logger.info(f"Analyzer: {analyzer.analyzer_name}")
        self.logger.info(f"Description: {analyzer.description}")
        self.logger.info(f"Raw Record Count: {metadata.get('raw_record_count', 0)}")
        self.logger.info(f"Query Parameters: {metadata.get('query_params', {})}")

        # Log structured data summary
        data_keys = [k for k in structured_data.keys() if not k.startswith("_")]
        self.logger.info(f"Structured Data Keys: {data_keys}")

        # Log sample of structured data
        if "activities" in structured_data:
            activities = structured_data["activities"]
            self.logger.info(f"Activities Count: {len(activities)}")
            if activities:
                self.logger.info(f"Sample Activity Keys: {list(activities[0].keys())}")

    def _export_debug_data(
        self,
        structured_data: Dict[str, Any],
        task_context: TaskContext,
        analyzer: BaseAnalyzer,
    ) -> None:
        """
        Export debug data to files for analysis.

        Args:
            structured_data: The structured data to export
            task_context: Task context for extracting metadata
            analyzer: The analyzer that was used
        """
        try:
            from pathlib import Path

            # Create export directory
            export_dir = Path("exports/salesforce_data_analyzer")
            export_dir.mkdir(parents=True, exist_ok=True)

            # Create filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            user_id = task_context.metadata.get("query_params", {}).get(
                "user_id", "unknown"
            )
            filename = f"{analyzer.analyzer_name}_{user_id}_{timestamp}.json"
            filepath = export_dir / filename

            # Export using the analyzer's export method
            analyzer.export_debug_data(structured_data, str(filepath))

            self.logger.info(f"Debug data exported to: {filepath}")

        except Exception as e:
            self.logger.error(f"Error exporting debug data: {str(e)}")

    def validate_analyzer_compatibility(self, analyzer: BaseAnalyzer, event) -> bool:
        """
        Validate that the analyzer is compatible with the event.

        Args:
            analyzer: The analyzer to validate
            event: The event data

        Returns:
            True if compatible, False otherwise
        """
        try:
            # Check if event has required parameters
            required_params = analyzer.get_required_parameters()

            for param in required_params:
                if not hasattr(event, param):
                    self.logger.warning(f"Event missing required parameter: {param}")
                    return False

            return True

        except Exception as e:
            self.logger.error(f"Error validating analyzer compatibility: {str(e)}")
            return False
