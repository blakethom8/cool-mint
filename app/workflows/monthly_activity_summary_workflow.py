"""
Monthly Activity Summary Workflow

This workflow generates comprehensive monthly activity summaries for healthcare
outreach specialists by analyzing their Salesforce activity data.
"""

from typing import Dict, Any

from app.core.schema import WorkflowSchema, NodeConfig
from app.core.workflow import Workflow
from app.core.task import TaskContext

from app.workflows.monthly_activity_summary_nodes.request_category_node import (
    RequestCategoryNode,
)
from app.workflows.monthly_activity_summary_nodes.sql_data_node import SQLDataNode
from app.workflows.monthly_activity_summary_nodes.data_structure_node import (
    DataStructureNode,
)
from app.workflows.monthly_activity_summary_nodes.llm_summary_node import LLMSummaryNode
from app.schemas.monthly_activity_summary_schema import MonthlyActivitySummaryEvent


class MonthlyActivitySummaryWorkflow(Workflow):
    """Workflow for generating monthly activity summaries."""

    workflow_schema = WorkflowSchema(
        description="Generates comprehensive monthly activity summaries from Salesforce data",
        event_schema=MonthlyActivitySummaryEvent,
        start=RequestCategoryNode,
        nodes=[
            NodeConfig(
                node=RequestCategoryNode,
                connections=[SQLDataNode],
                description="Categorizes the request type (currently hardcoded to monthly_summary)",
            ),
            NodeConfig(
                node=SQLDataNode,
                connections=[DataStructureNode],
                description="Executes SQL queries to retrieve activity data with proper joins",
            ),
            NodeConfig(
                node=DataStructureNode,
                connections=[LLMSummaryNode],
                description="Structures raw SQL data for optimal LLM consumption",
            ),
            NodeConfig(
                node=LLMSummaryNode,
                connections=[],
                description="Generates comprehensive activity summary using OpenAI",
            ),
        ],
    )

    @staticmethod
    def process(event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a monthly activity summary request.

        Args:
            event_data: Dictionary containing the MonthlyActivitySummaryEvent data

        Returns:
            Dictionary containing the workflow results
        """
        workflow = MonthlyActivitySummaryWorkflow()
        result = workflow.run(event_data)

        # Extract results from each node
        category_result = result.nodes.get("RequestCategoryNode", {}).get("result", {})
        sql_result = result.nodes.get("SQLDataNode", {}).get("result", {})
        structure_result = result.nodes.get("DataStructureNode", {}).get("result", {})
        llm_result = result.nodes.get("LLMSummaryNode", {}).get("result", {})

        # Format the final response
        return {
            "success": True,
            "workflow_type": "monthly_activity_summary",
            "user_id": event_data.get("user_id", ""),
            "session_id": event_data.get("session_id", ""),
            "summary_period": {
                "start_date": event_data.get("start_date"),
                "end_date": event_data.get("end_date"),
                "request_type": event_data.get("request_type", "monthly_summary"),
            },
            "request_category": {
                "determined_type": category_result.get("determined_type", ""),
                "confidence": category_result.get("confidence", 0.0),
            },
            "data_metrics": {
                "total_activities": sql_result.get("query_params", {}).get(
                    "total_activities", 0
                ),
                "activities_retrieved": len(sql_result.get("activities", [])),
                "unique_contacts": sql_result.get("basic_stats", {}).get(
                    "unique_contacts", 0
                )
                if sql_result
                else 0,
                "unique_organizations": sql_result.get("basic_stats", {}).get(
                    "unique_organizations", 0
                )
                if sql_result
                else 0,
                "individual_activities_formatted": len(
                    structure_result.get("activities", []) if structure_result else []
                ),
            },
            "summary": {
                "executive_summary": getattr(llm_result, "executive_summary", ""),
                "key_highlights_by_specialty": getattr(
                    llm_result, "key_highlights_by_specialty", {}
                ),
                "important_provider_relationships": getattr(
                    llm_result, "important_provider_relationships", []
                ),
                "key_discussion_themes": getattr(
                    llm_result, "key_discussion_themes", []
                ),
                "outreach_patterns_and_trends": getattr(
                    llm_result, "outreach_patterns_and_trends", {}
                ),
                "strategic_recommendations": getattr(
                    llm_result, "strategic_recommendations", []
                ),
                "performance_metrics": getattr(llm_result, "performance_metrics", {}),
                "areas_needing_attention": getattr(
                    llm_result, "areas_needing_attention", []
                ),
                "success_stories": getattr(llm_result, "success_stories", []),
                "next_month_priorities": getattr(
                    llm_result, "next_month_priorities", []
                ),
            },
            "processing_metadata": {
                "request_categorized": result.metadata.get(
                    "request_categorized", False
                ),
                "sql_data_retrieved": result.metadata.get("sql_data_retrieved", False),
                "data_structured": result.metadata.get("data_structured", False),
                "llm_summary_generated": result.metadata.get(
                    "llm_summary_generated", False
                ),
                "total_processing_nodes": 4,
                "errors": [
                    node_result.get("error")
                    for node_result in result.nodes.values()
                    if node_result.get("error")
                ],
            },
            "raw_data": {
                "category_result": category_result,
                "sql_summary": {
                    "query_params": sql_result.get("query_params", {}),
                    "basic_stats": sql_result.get("basic_stats", {}),
                    "activities_count": len(sql_result.get("activities", [])),
                },
                "structured_data_summary": {
                    "summary_period": structure_result.get("summary_period", {})
                    if structure_result
                    else {},
                    "basic_metrics": structure_result.get("basic_metrics", {})
                    if structure_result
                    else {},
                    "individual_activities_count": len(
                        structure_result.get("activities", [])
                        if structure_result
                        else []
                    ),
                },
            },
        }

    @staticmethod
    def create_test_event(
        user_id: str, start_date: str = None, end_date: str = None
    ) -> Dict[str, Any]:
        """
        Create a test event for the monthly activity summary workflow.

        Args:
            user_id: Salesforce user ID
            start_date: Optional start date (ISO format)
            end_date: Optional end date (ISO format)

        Returns:
            Dictionary containing test event data
        """
        event = {
            "user_id": user_id,
            "request_type": "monthly_summary",
            "session_id": f"test_session_{user_id}",
            "metadata": {"source": "test", "created_by": "workflow_test"},
        }

        if start_date:
            event["start_date"] = start_date
        if end_date:
            event["end_date"] = end_date

        return event
