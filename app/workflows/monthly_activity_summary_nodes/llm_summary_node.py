"""
LLM Summary Node

This node uses OpenAI to generate comprehensive activity summaries
based on structured activity data from the previous nodes.
"""

import json
import logging
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

from app.core.nodes.agent import AgentNode, AgentConfig, ModelProvider
from app.core.task import TaskContext
from app.services.prompt_loader import PromptManager


class ActivitySummaryOutput(BaseModel):
    """Output schema for activity summary generation."""

    executive_summary: str = Field(
        description="2-3 sentence executive summary of the month's outreach activities",
        min_length=100,
        max_length=500,
    )

    key_highlights_by_specialty: Dict[str, List[str]] = Field(
        description="Key highlights and insights organized by medical specialty",
        default_factory=dict,
    )

    important_provider_relationships: List[Dict[str, str]] = Field(
        description="List of important provider relationships and significant interactions",
        default_factory=list,
    )

    key_discussion_themes: List[str] = Field(
        description="Major themes and topics discussed during outreach activities",
        default_factory=list,
    )

    outreach_patterns_and_trends: Dict[str, Any] = Field(
        description="Patterns and trends observed in outreach activities",
        default_factory=dict,
    )

    strategic_recommendations: List[str] = Field(
        description="Actionable recommendations for improving future outreach efforts",
        default_factory=list,
    )

    performance_metrics: Dict[str, Any] = Field(
        description="Key performance metrics and statistics", default_factory=dict
    )

    areas_needing_attention: List[str] = Field(
        description="Areas or specialties that may need more attention",
        default_factory=list,
    )

    success_stories: List[str] = Field(
        description="Notable success stories or breakthrough moments",
        default_factory=list,
    )

    next_month_priorities: List[str] = Field(
        description="Recommended priorities for the upcoming month",
        default_factory=list,
    )


class LLMSummaryNode(AgentNode):
    """Node that generates comprehensive activity summaries using OpenAI."""

    def __init__(self):
        self.prompt_loader = PromptManager()
        # Load the prompt data before initializing parent
        self.prompt_data = self.prompt_loader.get_prompt(
            "monthly_activity_summary/activity_summary"
        )
        super().__init__()
        self.logger = logging.getLogger(__name__)

    def get_agent_config(self) -> AgentConfig:
        """Configure the agent for activity summary generation."""
        return AgentConfig(
            system_prompt=self.prompt_data.system_prompt,
            output_type=ActivitySummaryOutput,
            deps_type=None,
            model_provider=ModelProvider(self.prompt_data.model.provider),
            model_name=self.prompt_data.model.name,
            instrument=True,
        )

    def process(self, task_context: TaskContext) -> TaskContext:
        """
        Generate comprehensive activity summary using OpenAI.

        Args:
            task_context: Task context containing structured data from previous nodes

        Returns:
            Updated task context with generated summary
        """
        try:
            # Get structured data from previous node
            structured_data = task_context.nodes.get("DataStructureNode", {}).get(
                "result"
            )
            if not structured_data:
                raise ValueError("No structured data found from previous node")

            self.logger.info("Generating individual activity analysis using OpenAI")

            # Prepare the user prompt with structured data
            user_prompt = self._create_user_prompt(structured_data, task_context)

            # Capture prompts for tracing
            self._capture_prompts(task_context, user_prompt)

            # Generate summary using the agent
            result = self.agent.run_sync(user_prompt=user_prompt)

            # Store the summary result
            task_context.update_node(node_name=self.node_name, result=result.data)
            task_context.metadata["llm_summary_generated"] = True
            task_context.metadata["summary_length"] = len(result.data.executive_summary)
            task_context.metadata["specialties_analyzed"] = len(
                result.data.key_highlights_by_specialty
            )
            task_context.metadata["individual_activities_analyzed"] = len(
                structured_data.get("activities", [])
            )

            # Store the completion if available
            if hasattr(result, "completion"):
                task_context.metadata["completion"] = result.completion

            self.logger.info("Individual activity analysis successfully generated")

            return task_context

        except Exception as e:
            self.logger.error(f"Error generating LLM summary: {str(e)}")
            task_context.update_node(
                node_name=self.node_name, error=str(e), result=None
            )
            task_context.metadata["llm_summary_generated"] = False
            task_context.metadata["error"] = str(e)
            return task_context

    def _create_user_prompt(
        self, structured_data: Dict[str, Any], task_context: TaskContext
    ) -> str:
        """
        Create the user prompt with individual activity data.

        NEW: Focuses on individual activity analysis with complete contact context.

        Args:
            structured_data: Structured activity data from previous node
            task_context: Task context with additional metadata

        Returns:
            Formatted user prompt for the LLM
        """
        # Extract key information
        summary_period = structured_data.get("summary_period", {})
        basic_metrics = structured_data.get("basic_metrics", {})
        activities = structured_data.get("activities", [])

        # Create comprehensive prompt focused on individual activities
        prompt = f"""
Please analyze the following monthly activity data and provide a comprehensive summary:

## SUMMARY PERIOD
- Period: {summary_period.get("start_date")} to {summary_period.get("end_date")}
- Total Days: {summary_period.get("total_days")}
- User ID: {summary_period.get("user_id")}

## BASIC METRICS
- Total Activities: {basic_metrics.get("total_activities", 0)}
- Unique Contacts: {basic_metrics.get("unique_contacts", 0)}
- Unique Organizations: {basic_metrics.get("unique_organizations", 0)}
- Date Range: {basic_metrics.get("date_range", "")}

## INDIVIDUAL ACTIVITIES ANALYSIS

"""

        # Add each individual activity with complete context
        for i, activity in enumerate(
            activities[:50], 1
        ):  # Limit to 50 activities to avoid token limits
            activity_info = activity.get("activity_info", {})
            contact_info = activity.get("contact_info", {})

            prompt += f"""
### Activity {i} - {activity_info.get("activity_date", "Unknown Date")}
**Activity Type**: {activity_info.get("mno_type", "Unknown")} - {activity_info.get("mno_subtype", "Unknown")}
**Subject**: {activity_info.get("subject", "No subject")}
**Priority**: {activity_info.get("priority", "Unknown")}
**Status**: {activity_info.get("status", "Unknown")}

**Provider Information**:
- **Name**: {contact_info.get("name", "Unknown")}
- **Title**: {contact_info.get("title", "Unknown")}
- **Organization**: {contact_info.get("contact_account_name", "Unknown")}
- **Location**: {contact_info.get("mailing_city", "Unknown")}
- **Geography**: {contact_info.get("mn_primary_geography", "Unknown")}
- **Specialty**: {contact_info.get("specialty", "Unknown")}
- **MGMA Specialty**: {contact_info.get("mn_mgma_specialty", "Unknown")}
- **Specialty Group**: {contact_info.get("mn_specialty_group", "Unknown")}
- **Employment Status**: {contact_info.get("employment_status", "Unknown")}
- **Provider Type**: {contact_info.get("provider_type", "Unknown")}
- **Is Physician**: {contact_info.get("is_physician", "Unknown")}

**Activity Details**:
{activity_info.get("description", "No description provided")}

**Additional Notes**: {activity_info.get("comments_short", "No additional comments")}
**Tags**: {activity_info.get("mn_tags", "No tags")}

---

"""

        # Add analysis request
        prompt += """
## ANALYSIS REQUEST
Based on this detailed activity information, please provide:

1. **Executive Summary**: A comprehensive overview of the month's outreach activities
2. **Key Highlights by Specialty**: Organize insights by medical specialty, highlighting key interactions and outcomes
3. **Important Provider Relationships**: Identify significant relationships and interactions with providers
4. **Discussion Themes**: Extract major themes and topics from the activity descriptions
5. **Outreach Patterns**: Identify patterns in outreach activities, geographic focus, and engagement strategies
6. **Strategic Recommendations**: Provide actionable recommendations for improving future outreach efforts
7. **Performance Metrics**: Summarize key performance indicators and engagement metrics
8. **Areas Needing Attention**: Identify specialties, regions, or provider types that may need more focus
9. **Success Stories**: Highlight notable successes or breakthrough moments from the activities
10. **Next Month Priorities**: Recommend priorities and focus areas for the upcoming month

Please focus on actionable insights that will help improve outreach effectiveness and strengthen provider relationships. Consider the specific provider context, geographic distribution, and activity details in your analysis.
"""

        return prompt

    def _format_activities_by_specialty(
        self, activities_by_specialty: Dict[str, List[Dict[str, Any]]]
    ) -> str:
        """Format activities by specialty for the prompt."""
        formatted = ""

        for specialty, activities in activities_by_specialty.items():
            formatted += f"\n### {specialty}\n"
            for activity in activities[:5]:  # Top 5 activities per specialty
                formatted += f"- {activity.get('contact_name', 'Unknown')} ({activity.get('activity_date')}): {activity.get('subject', 'No subject')}\n"
                if activity.get("description"):
                    formatted += (
                        f"  Description: {activity.get('description', '')[:200]}...\n"
                    )

        return formatted
