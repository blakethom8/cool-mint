"""
Request Category Node

This node categorizes the type of request being made. Currently hardcoded to
"monthly_summary" but designed to be extensible for future request types.
"""

import logging
from typing import Dict, Any

from core.nodes.base import Node
from core.task import TaskContext


class RequestCategoryNode(Node):
    """Node that categorizes the request type."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def process(self, task_context: TaskContext) -> TaskContext:
        """
        Categorize the request type.

        Args:
            task_context: Task context containing the event data

        Returns:
            Updated task context with request category
        """
        try:
            # For now, hardcode to monthly_summary
            # In the future, this could analyze the request and determine the type
            request_type = "monthly_summary"

            # Extract some basic info from the event
            user_id = task_context.event.user_id
            original_request_type = task_context.event.request_type

            self.logger.info(
                f"Categorizing request for user {user_id} as {request_type}"
            )

            # Create categorization result
            categorization_result = {
                "determined_type": request_type,
                "original_request_type": original_request_type,
                "user_id": user_id,
                "confidence": 1.0,  # High confidence since it's hardcoded
                "category_metadata": {
                    "supports_date_range": True,
                    "requires_activity_data": True,
                    "supports_specialty_analysis": True,
                    "supports_contact_analysis": True,
                    "output_format": "comprehensive_summary",
                },
            }

            # Store categorization result
            task_context.update_node(
                node_name=self.node_name, result=categorization_result
            )
            task_context.metadata["request_categorized"] = True
            task_context.metadata["category"] = request_type

            self.logger.info(f"Request successfully categorized as {request_type}")

            return task_context

        except Exception as e:
            self.logger.error(f"Error categorizing request: {str(e)}")
            task_context.update_node(
                node_name=self.node_name, error=str(e), result=None
            )
            task_context.metadata["request_categorized"] = False
            task_context.metadata["error"] = str(e)
            return task_context

    def _analyze_request_type(self, event) -> str:
        """
        Analyze the incoming event to determine request type.

        This is a placeholder for future enhancement where we might use
        NLP or rule-based classification to determine the request type.

        Args:
            event: The incoming event data

        Returns:
            String representing the request type
        """
        # Future enhancement: implement intelligent request type detection
        # Could analyze text patterns, date ranges, or other indicators

        # For now, return the hardcoded value
        return "monthly_summary"

    def _get_category_metadata(self, request_type: str) -> Dict[str, Any]:
        """
        Get metadata for the categorized request type.

        Args:
            request_type: The categorized request type

        Returns:
            Dictionary containing metadata about the request type
        """
        category_configs = {
            "monthly_summary": {
                "supports_date_range": True,
                "requires_activity_data": True,
                "supports_specialty_analysis": True,
                "supports_contact_analysis": True,
                "output_format": "comprehensive_summary",
                "typical_date_range_days": 30,
                "requires_llm_analysis": True,
            },
            # Future request types could be added here
            # 'weekly_summary': { ... },
            # 'specialty_focus': { ... },
            # 'contact_analysis': { ... }
        }

        return category_configs.get(request_type, {})
