"""
Request Category Node

This node analyzes the incoming request and selects the appropriate analyzer
from the available analyzers registry.
"""

import logging
from typing import Dict, Any, Optional

from core.nodes.base import Node
from core.task import TaskContext
from workflows.salesforce_data_analyzer.analyzers import (
    BaseAnalyzer,
    MonthlyActivitySummaryAnalyzer,
)


class AnalyzerRegistry:
    """Registry for available analyzers."""

    def __init__(self):
        self._analyzers = {
            "monthly_activity_summary": MonthlyActivitySummaryAnalyzer,
            "monthly_summary": MonthlyActivitySummaryAnalyzer,  # Alias
            "activity_summary": MonthlyActivitySummaryAnalyzer,  # Alias
        }

    def get_analyzer(
        self, request_type: str, debug_mode: bool = False
    ) -> Optional[BaseAnalyzer]:
        """
        Get analyzer instance for the given request type.

        Args:
            request_type: Type of request to analyze
            debug_mode: Whether to enable debug mode

        Returns:
            Analyzer instance or None if not found
        """
        analyzer_class = self._analyzers.get(request_type.lower())
        if analyzer_class:
            return analyzer_class(debug_mode=debug_mode)
        return None

    def get_available_analyzers(self) -> Dict[str, str]:
        """
        Get dictionary of available analyzers and their descriptions.

        Returns:
            Dictionary mapping analyzer names to descriptions
        """
        result = {}
        for name, analyzer_class in self._analyzers.items():
            try:
                instance = analyzer_class()
                result[name] = instance.description
            except Exception:
                result[name] = f"Analyzer: {analyzer_class.__name__}"
        return result


class RequestCategoryNode(Node):
    """
    Node that categorizes incoming requests and selects the appropriate analyzer.

    This node:
    1. Analyzes the request type from the event
    2. Selects the appropriate analyzer from the registry
    3. Stores the analyzer in task context for use by unified SQL data node
    """

    def __init__(self, debug_mode: bool = False):
        self.debug_mode = debug_mode
        self.logger = logging.getLogger(__name__)
        self.analyzer_registry = AnalyzerRegistry()

    def process(self, task_context: TaskContext) -> TaskContext:
        """
        Analyze the request and select the appropriate analyzer.

        Args:
            task_context: Task context containing the event data

        Returns:
            Updated task context with selected analyzer
        """
        try:
            # Extract request type from event
            request_type = self._extract_request_type(task_context)

            self.logger.info(f"Processing request type: {request_type}")

            # Get analyzer for the request type
            analyzer = self.analyzer_registry.get_analyzer(
                request_type, debug_mode=self.debug_mode
            )

            if not analyzer:
                available_analyzers = self.analyzer_registry.get_available_analyzers()
                raise ValueError(
                    f"No analyzer found for request type: {request_type}. "
                    f"Available analyzers: {list(available_analyzers.keys())}"
                )

            # Store analyzer in task context
            task_context.metadata["selected_analyzer"] = analyzer
            task_context.metadata["request_type"] = request_type
            task_context.metadata["analyzer_name"] = analyzer.analyzer_name
            task_context.metadata["analyzer_description"] = analyzer.description

            # Store results in task context
            task_context.update_node(
                node_name=self.node_name,
                result={
                    "request_type": request_type,
                    "analyzer_name": analyzer.analyzer_name,
                    "analyzer_description": analyzer.description,
                    "analyzer_selected": True,
                },
            )

            if self.debug_mode:
                self.logger.info(f"Selected analyzer: {analyzer.analyzer_name}")
                self.logger.info(f"Analyzer description: {analyzer.description}")

            return task_context

        except Exception as e:
            self.logger.error(f"Error in request category node: {str(e)}")
            task_context.update_node(
                node_name=self.node_name, error=str(e), result=None
            )
            task_context.metadata["analyzer_selected"] = False
            task_context.metadata["error"] = str(e)
            return task_context

    def _extract_request_type(self, task_context: TaskContext) -> str:
        """
        Extract the request type from the task context event.

        Args:
            task_context: Task context containing event data

        Returns:
            Request type string
        """
        event = task_context.event

        # Check for explicit request_type field
        if hasattr(event, "request_type") and event.request_type:
            return event.request_type

        # Check for analysis_type field
        if hasattr(event, "analysis_type") and event.analysis_type:
            return event.analysis_type

        # Check for workflow_type field
        if hasattr(event, "workflow_type") and event.workflow_type:
            return event.workflow_type

        # Default to monthly activity summary if no specific type is provided
        self.logger.warning(
            "No request type specified in event, defaulting to monthly_activity_summary"
        )
        return "monthly_activity_summary"

    def get_available_analyzers(self) -> Dict[str, str]:
        """
        Get available analyzers for external use.

        Returns:
            Dictionary of available analyzers
        """
        return self.analyzer_registry.get_available_analyzers()

    def validate_request(self, task_context: TaskContext) -> tuple[bool, str]:
        """
        Validate that the request can be processed.

        Args:
            task_context: Task context to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            event = task_context.event

            # Check if event has basic required fields
            if not hasattr(event, "user_id") or not event.user_id:
                return False, "Event missing required field: user_id"

            # Check if request type is supported
            request_type = self._extract_request_type(task_context)
            analyzer = self.analyzer_registry.get_analyzer(request_type)

            if not analyzer:
                available = list(
                    self.analyzer_registry.get_available_analyzers().keys()
                )
                return (
                    False,
                    f"Unsupported request type: {request_type}. Available: {available}",
                )

            # Check if analyzer requirements are met
            required_params = analyzer.get_required_parameters()
            for param in required_params:
                if not hasattr(event, param):
                    return (
                        False,
                        f"Event missing required parameter for {request_type}: {param}",
                    )

            return True, ""

        except Exception as e:
            return False, f"Validation error: {str(e)}"
