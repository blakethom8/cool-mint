"""
Salesforce Data Analyzer Workflow

Main workflow that coordinates the analysis of Salesforce data using the
modular analyzer pattern. This workflow properly handles complex relationships
between Activities and Contacts through the TaskWhoRelation table.
"""

import logging
from typing import Dict, Any

from core.workflow import Workflow
from core.task import TaskContext
from .nodes import RequestCategoryNode, UnifiedSQLDataNode


class SalesforceDataAnalyzerWorkflow(Workflow):
    """
    Dynamic workflow for analyzing Salesforce data.

    This workflow uses a modular approach where:
    1. RequestCategoryNode selects the appropriate analyzer based on request type
    2. UnifiedSQLDataNode executes the analyzer's SQL query and structures the data
    3. Results are available for further processing (e.g., LLM analysis)

    Key improvements over the old system:
    - Handles multiple contacts per activity properly
    - Modular analyzer pattern for extensibility
    - Combined SQL + Data Structuring for consistency
    - Dynamic analyzer selection based on request type
    """

    def __init__(self, debug_mode: bool = False, export_debug_data: bool = False):
        self.debug_mode = debug_mode
        self.export_debug_data = export_debug_data
        self.logger = logging.getLogger(__name__)

        # Initialize nodes
        self.request_category_node = RequestCategoryNode(debug_mode=debug_mode)
        self.unified_sql_data_node = UnifiedSQLDataNode(
            debug_mode=debug_mode, export_debug_data=export_debug_data
        )

        # Node names are automatically set by the base Node class

    @property
    def workflow_name(self) -> str:
        return "SalesforceDataAnalyzer"

    def run(self, event_data: Dict[str, Any]) -> TaskContext:
        """
        Execute the Salesforce data analysis workflow.

        Args:
            event_data: Event data containing analysis parameters

        Returns:
            TaskContext with analysis results
        """
        self.logger.info(f"Starting {self.workflow_name} workflow")

        # Create task context
        task_context = TaskContext(event=self._create_event_from_dict(event_data))
        task_context.metadata["workflow_name"] = self.workflow_name
        task_context.metadata["debug_mode"] = self.debug_mode
        task_context.metadata["export_debug_data"] = self.export_debug_data

        try:
            # Step 1: Categorize request and select analyzer
            self.logger.info("Step 1: Analyzing request and selecting analyzer")
            task_context = self.request_category_node.process(task_context)

            # Check if analyzer selection was successful
            if task_context.nodes.get("RequestCategoryNode", {}).get("error"):
                self.logger.error("Failed to select analyzer")
                return task_context

            analyzer_name = task_context.metadata.get("analyzer_name", "Unknown")
            self.logger.info(f"Selected analyzer: {analyzer_name}")

            # Step 2: Execute analyzer query and structure data
            self.logger.info("Step 2: Executing SQL query and structuring data")
            task_context = self.unified_sql_data_node.process(task_context)

            # Check if data retrieval was successful
            if task_context.nodes.get("UnifiedSQLDataNode", {}).get("error"):
                self.logger.error("Failed to retrieve and structure data")
                return task_context

            # Log success metrics
            raw_record_count = task_context.metadata.get("raw_record_count", 0)
            self.logger.info(f"Successfully processed {raw_record_count} raw records")

            # Mark workflow as completed
            task_context.metadata["workflow_completed"] = True
            task_context.metadata["workflow_success"] = True

            self.logger.info(f"{self.workflow_name} workflow completed successfully")

            return task_context

        except Exception as e:
            self.logger.error(f"Error in {self.workflow_name} workflow: {str(e)}")
            task_context.metadata["workflow_completed"] = True
            task_context.metadata["workflow_success"] = False
            task_context.metadata["workflow_error"] = str(e)
            return task_context

    def _create_event_from_dict(self, event_data: Dict[str, Any]) -> Any:
        """
        Create an event object from dictionary data.

        Args:
            event_data: Dictionary containing event parameters

        Returns:
            Event object with attributes set from the dictionary
        """
        from types import SimpleNamespace

        # Convert dictionary to an object with attributes
        event = SimpleNamespace()

        # Set attributes from the dictionary
        for key, value in event_data.items():
            setattr(event, key, value)

        return event

    def get_available_analyzers(self) -> Dict[str, str]:
        """
        Get available analyzers from the request category node.

        Returns:
            Dictionary of available analyzers and their descriptions
        """
        return self.request_category_node.get_available_analyzers()

    def validate_event(self, event_data: Dict[str, Any]) -> tuple[bool, str]:
        """
        Validate that the event data is valid for this workflow.

        Args:
            event_data: Event data to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Create temporary task context for validation
            event = self._create_event_from_dict(event_data)
            temp_context = TaskContext(event=event)

            # Use request category node to validate
            return self.request_category_node.validate_request(temp_context)

        except Exception as e:
            return False, f"Validation error: {str(e)}"

    def export_workflow_metadata(self) -> Dict[str, Any]:
        """
        Export metadata about this workflow for documentation purposes.

        Returns:
            Dictionary containing workflow metadata
        """
        return {
            "workflow_name": self.workflow_name,
            "description": self.__doc__.strip().split("\n")[0] if self.__doc__ else "",
            "nodes": [
                {
                    "name": "RequestCategoryNode",
                    "description": "Analyzes request and selects appropriate analyzer",
                    "class": self.request_category_node.__class__.__name__,
                },
                {
                    "name": "UnifiedSQLDataNode",
                    "description": "Executes SQL query and structures data using selected analyzer",
                    "class": self.unified_sql_data_node.__class__.__name__,
                },
            ],
            "available_analyzers": self.get_available_analyzers(),
            "features": [
                "Handles multiple contacts per activity through TaskWhoRelation",
                "Modular analyzer pattern for extensibility",
                "Combined SQL + Data Structuring",
                "Dynamic analyzer selection",
            ],
        }
