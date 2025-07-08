"""
Data Structure Node

This node takes raw SQL data and structures it for optimal LLM consumption,
creating organized summaries and groupings that facilitate analysis.
"""

import json
import logging
from datetime import datetime, date
from typing import Dict, List, Any, Optional
from collections import defaultdict
from pathlib import Path

from app.core.nodes.base import Node
from app.core.task import TaskContext


class DataStructureNode(Node):
    """Node that structures raw SQL data for LLM analysis."""

    def __init__(self, debug_mode: bool = False, export_structured_data: bool = False):
        self.logger = logging.getLogger(__name__)
        self.debug_mode = debug_mode
        self.export_structured_data = export_structured_data

    def process(self, task_context: TaskContext) -> TaskContext:
        """
        Structure the raw SQL data for LLM consumption.

        Args:
            task_context: Task context containing SQL data from previous node

        Returns:
            Updated task context with structured data
        """
        try:
            # Get SQL data from previous node
            sql_data = task_context.nodes.get("SQLDataNode", {}).get("result")
            if not sql_data:
                raise ValueError("No SQL data found from previous node")

            self.logger.info("Structuring individual activities for LLM analysis")

            # Structure the data
            structured_data = self._create_structured_data(sql_data)

            # Debug logging and export
            if self.debug_mode:
                self._log_structured_data_summary(structured_data)

            if self.export_structured_data:
                self._export_structured_data(structured_data, task_context)

            # Store structured data in task context
            task_context.update_node(node_name=self.node_name, result=structured_data)
            task_context.metadata["data_structured"] = True
            task_context.metadata["structured_summary"] = {
                "total_activities": structured_data.get("summary_period", {}).get(
                    "total_activities", 0
                ),
                "unique_contacts": structured_data.get("basic_metrics", {}).get(
                    "unique_contacts", 0
                ),
                "unique_organizations": structured_data.get("basic_metrics", {}).get(
                    "unique_organizations", 0
                ),
                "individual_activities_formatted": len(
                    structured_data.get("activities", [])
                ),
            }

            self.logger.info(
                "Individual activities successfully structured for LLM analysis"
            )

            return task_context

        except Exception as e:
            self.logger.error(f"Error structuring data: {str(e)}")
            task_context.update_node(
                node_name=self.node_name, error=str(e), result=None
            )
            task_context.metadata["data_structured"] = False
            task_context.metadata["error"] = str(e)
            return task_context

    def _log_structured_data_summary(self, structured_data: Dict[str, Any]) -> None:
        """Log a summary of the structured data for debugging."""
        summary_period = structured_data.get("summary_period", {})
        basic_metrics = structured_data.get("basic_metrics", {})
        activities = structured_data.get("activities", [])

        self.logger.info("=== STRUCTURED DATA SUMMARY ===")
        self.logger.info(
            f"Period: {summary_period.get('start_date')} to {summary_period.get('end_date')}"
        )
        self.logger.info(
            f"Total Activities: {basic_metrics.get('total_activities', 0)}"
        )
        self.logger.info(f"Unique Contacts: {basic_metrics.get('unique_contacts', 0)}")
        self.logger.info(
            f"Unique Organizations: {basic_metrics.get('unique_organizations', 0)}"
        )
        self.logger.info(f"Individual Activities Formatted: {len(activities)}")

        # Log sample activities
        if activities:
            self.logger.info(f"=== SAMPLE ACTIVITIES (first 3) ===")
            for i, activity in enumerate(activities[:3], 1):
                activity_info = activity.get("activity_info", {})
                contact_info = activity.get("contact_info", {})
                self.logger.info(f"Activity {i}:")
                self.logger.info(f"  Date: {activity_info.get('activity_date')}")
                self.logger.info(
                    f"  Type: {activity_info.get('mno_type')} - {activity_info.get('mno_subtype')}"
                )
                self.logger.info(
                    f"  Contact: {contact_info.get('name')} ({contact_info.get('specialty')})"
                )
                self.logger.info(
                    f"  Organization: {contact_info.get('contact_account_name')}"
                )
                self.logger.info(f"  Subject: {activity_info.get('subject')}")
                self.logger.info(
                    f"  Description Length: {len(activity_info.get('description', ''))}"
                )

        # Log specialty distribution
        specialty_counts = {}
        for activity in activities:
            specialty = activity.get("contact_info", {}).get("specialty", "Unknown")
            specialty_counts[specialty] = specialty_counts.get(specialty, 0) + 1

        self.logger.info(f"=== SPECIALTY DISTRIBUTION ===")
        for specialty, count in sorted(
            specialty_counts.items(), key=lambda x: x[1], reverse=True
        ):
            self.logger.info(f"  {specialty}: {count} activities")

    def _export_structured_data(
        self, structured_data: Dict[str, Any], task_context: TaskContext
    ) -> None:
        """Export structured data to a JSON file for analysis."""
        try:
            # Create exports directory if it doesn't exist
            export_dir = Path("exports/structured_data")
            export_dir.mkdir(parents=True, exist_ok=True)

            # Create filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            user_id = task_context.event.user_id
            filename = f"structured_data_{user_id}_{timestamp}.json"
            filepath = export_dir / filename

            # Export data
            with open(filepath, "w") as f:
                json.dump(structured_data, f, indent=2, default=str)

            self.logger.info(f"Structured data exported to: {filepath}")

            # Also export a summary for quick analysis
            summary_filename = f"structured_summary_{user_id}_{timestamp}.json"
            summary_filepath = export_dir / summary_filename

            summary = {
                "metadata": {
                    "export_timestamp": timestamp,
                    "user_id": user_id,
                    "period": f"{structured_data.get('summary_period', {}).get('start_date')} to {structured_data.get('summary_period', {}).get('end_date')}",
                },
                "metrics": structured_data.get("basic_metrics", {}),
                "summary_period": structured_data.get("summary_period", {}),
                "activity_count": len(structured_data.get("activities", [])),
                "sample_activities": structured_data.get("activities", [])[
                    :5
                ],  # First 5 for quick review
                "specialty_distribution": self._get_specialty_distribution(
                    structured_data.get("activities", [])
                ),
                "contact_distribution": self._get_contact_distribution(
                    structured_data.get("activities", [])
                ),
            }

            with open(summary_filepath, "w") as f:
                json.dump(summary, f, indent=2, default=str)

            self.logger.info(f"Structured data summary exported to: {summary_filepath}")

        except Exception as e:
            self.logger.error(f"Error exporting structured data: {str(e)}")

    def _get_specialty_distribution(
        self, activities: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """Get distribution of activities by specialty."""
        distribution = {}
        for activity in activities:
            specialty = activity.get("contact_info", {}).get("specialty", "Unknown")
            distribution[specialty] = distribution.get(specialty, 0) + 1
        return dict(sorted(distribution.items(), key=lambda x: x[1], reverse=True))

    def _get_contact_distribution(
        self, activities: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """Get distribution of activities by contact."""
        distribution = {}
        for activity in activities:
            contact = activity.get("contact_info", {}).get("name", "Unknown")
            distribution[contact] = distribution.get(contact, 0) + 1
        return dict(sorted(distribution.items(), key=lambda x: x[1], reverse=True))

    def _create_structured_data(self, sql_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create structured data from raw SQL results.

        NEW: Simplified version focused on individual activity details
        rather than complex aggregations.

        Args:
            sql_data: Raw SQL data from database queries

        Returns:
            Structured data optimized for individual activity analysis
        """
        activities = sql_data.get("activities", [])
        basic_stats = sql_data.get("basic_stats", {})
        query_params = sql_data.get("query_params", {})

        # Create simplified activity-focused structure
        structured_data = {
            "summary_period": {
                "start_date": query_params.get("start_date"),
                "end_date": query_params.get("end_date"),
                "user_id": query_params.get("user_id"),
                "total_activities": len(activities),
                "total_days": self._calculate_date_range_days(
                    query_params.get("start_date"), query_params.get("end_date")
                ),
            },
            "basic_metrics": {
                "total_activities": basic_stats.get("total_activities", 0),
                "unique_contacts": basic_stats.get("unique_contacts", 0),
                "unique_organizations": basic_stats.get("unique_organizations", 0),
                "date_range": basic_stats.get("date_range", ""),
            },
            "activities": self._format_individual_activities(activities),
        }

        return structured_data

    def _format_individual_activities(
        self, activities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Format individual activities with complete contact information.

        NEW: Creates structured activity records with activity info and contact context.

        Args:
            activities: List of activity records from database

        Returns:
            List of formatted activity records with structured info
        """
        formatted_activities = []

        for activity in activities:
            # Structure activity information
            activity_info = {
                "activity_date": activity.get("activity_date"),
                "mno_type": activity.get("mno_type"),
                "mno_subtype": activity.get("mno_subtype"),
                "description": activity.get("description"),
                "subject": activity.get("subject"),
                "status": activity.get("status"),
                "priority": activity.get("priority"),
                "activity_type": activity.get("activity_type"),
                "mn_tags": activity.get("mn_tags"),
                "comments_short": activity.get("comments_short"),
            }

            # Structure contact information
            contact_info = {
                "name": activity.get("contact_name"),
                "mailing_city": activity.get("mailing_city"),
                "specialty": activity.get("specialty"),
                "contact_account_name": activity.get("contact_account_name"),
                "employment_status": activity.get("employment_status"),
                "mn_mgma_specialty": activity.get("mn_mgma_specialty"),
                "mn_primary_geography": activity.get("mn_primary_geography"),
                "mn_specialty_group": activity.get("mn_specialty_group"),
                "title": activity.get("contact_title"),
                "is_physician": activity.get("is_physician"),
                "provider_type": activity.get("provider_type"),
                "email": activity.get("contact_email"),
                "phone": activity.get("contact_phone"),
            }

            # Create combined activity record
            formatted_activity = {
                "activity_info": activity_info,
                "contact_info": contact_info,
            }

            formatted_activities.append(formatted_activity)

        return formatted_activities

    def _format_overall_metrics(self, summary_stats: Dict[str, Any]) -> Dict[str, Any]:
        """Format overall activity metrics."""
        return {
            "total_activities": summary_stats.get("total_activities", 0),
            "unique_contacts": summary_stats.get("unique_contacts", 0),
            "unique_specialties": summary_stats.get("unique_specialties", 0),
            "unique_organizations": summary_stats.get("unique_organizations", 0),
            "active_days": summary_stats.get("active_days", 0),
            "activity_types": {
                "tasks": summary_stats.get("task_count", 0),
                "events": summary_stats.get("event_count", 0),
            },
            "priority_distribution": {
                "high": summary_stats.get("high_priority_count", 0),
                "normal": summary_stats.get("normal_priority_count", 0),
                "low": summary_stats.get("low_priority_count", 0),
            },
            "completion_status": {
                "closed": summary_stats.get("closed_activities", 0),
                "open": summary_stats.get("open_activities", 0),
            },
        }

    def _group_activities_by_specialty(
        self, activities: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Group activities by provider specialty."""
        specialty_groups = defaultdict(list)

        for activity in activities:
            specialty = activity.get("specialty") or "Unknown"
            specialty_groups[specialty].append(
                {
                    "activity_date": activity.get("activity_date"),
                    "contact_name": activity.get("contact_name"),
                    "contact_title": activity.get("contact_title"),
                    "contact_organization": activity.get("contact_account_name"),
                    "subject": activity.get("subject"),
                    "description": activity.get("description"),
                    "priority": activity.get("priority"),
                    "status": activity.get("status"),
                    "activity_type": activity.get("activity_type"),
                    "mno_type": activity.get("mno_type"),
                    "geography": activity.get("geography"),
                }
            )

        # Sort activities within each specialty by date (most recent first)
        for specialty in specialty_groups:
            specialty_groups[specialty].sort(
                key=lambda x: x.get("activity_date", ""), reverse=True
            )

        return dict(specialty_groups)

    def _group_activities_by_contact(
        self, activities: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """Group activities by contact with summary information."""
        contact_groups = defaultdict(
            lambda: {
                "contact_info": {},
                "activities": [],
                "summary": {
                    "total_activities": 0,
                    "latest_activity": None,
                    "activity_types": defaultdict(int),
                    "priority_counts": defaultdict(int),
                },
            }
        )

        for activity in activities:
            contact_name = activity.get("contact_name") or "Unknown Contact"
            contact_data = contact_groups[contact_name]

            # Store contact info (only once)
            if not contact_data["contact_info"]:
                contact_data["contact_info"] = {
                    "name": contact_name,
                    "specialty": activity.get("specialty"),
                    "title": activity.get("contact_title"),
                    "organization": activity.get("contact_account_name"),
                    "geography": activity.get("geography"),
                    "is_physician": activity.get("is_physician"),
                }

            # Add activity
            contact_data["activities"].append(
                {
                    "activity_date": activity.get("activity_date"),
                    "subject": activity.get("subject"),
                    "description": activity.get("description"),
                    "priority": activity.get("priority"),
                    "status": activity.get("status"),
                    "activity_type": activity.get("activity_type"),
                }
            )

            # Update summary
            contact_data["summary"]["total_activities"] += 1
            if (
                not contact_data["summary"]["latest_activity"]
                or activity.get("activity_date", "")
                > contact_data["summary"]["latest_activity"]
            ):
                contact_data["summary"]["latest_activity"] = activity.get(
                    "activity_date"
                )

            contact_data["summary"]["activity_types"][
                activity.get("activity_type", "Unknown")
            ] += 1
            contact_data["summary"]["priority_counts"][
                activity.get("priority", "Unknown")
            ] += 1

        # Sort activities within each contact by date (most recent first)
        for contact in contact_groups:
            contact_groups[contact]["activities"].sort(
                key=lambda x: x.get("activity_date", ""), reverse=True
            )

        return dict(contact_groups)

    def _format_specialty_insights(
        self, specialty_breakdown: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Format specialty breakdown insights."""
        return [
            {
                "specialty": item.get("specialty"),
                "activity_count": item.get("activity_count", 0),
                "unique_contacts": item.get("unique_contacts", 0),
                "unique_organizations": item.get("unique_organizations", 0),
                "recent_activities": item.get("recent_activities", 0),
                "last_activity_date": item.get("last_activity_date"),
                "high_priority_count": item.get("high_priority_count", 0),
                "sample_contacts": item.get("sample_contacts", "").split(", ")[:3]
                if item.get("sample_contacts")
                else [],
            }
            for item in specialty_breakdown
        ]

    def _format_contact_insights(
        self, contact_summary: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Format contact summary insights."""
        return [
            {
                "contact_name": item.get("contact_name"),
                "specialty": item.get("specialty"),
                "organization": item.get("contact_account_name"),
                "title": item.get("title"),
                "geography": item.get("geography"),
                "is_physician": item.get("is_physician", False),
                "total_activities": item.get("total_activities", 0),
                "last_activity_date": item.get("last_activity_date"),
                "first_activity_date": item.get("first_activity_date"),
                "activity_types": {
                    "tasks": item.get("task_count", 0),
                    "events": item.get("event_count", 0),
                },
                "high_priority_count": item.get("high_priority_count", 0),
                "recent_activities": item.get("recent_activities", 0),
                "sample_subjects": item.get("sample_subjects", "").split(" | ")[:3]
                if item.get("sample_subjects")
                else [],
            }
            for item in contact_summary
        ]

    def _create_activity_timeline(
        self, activities: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create a timeline view of activities."""
        timeline = defaultdict(int)

        for activity in activities:
            activity_date = activity.get("activity_date")
            if activity_date:
                timeline[activity_date] += 1

        return {
            "daily_counts": dict(timeline),
            "most_active_day": max(timeline.items(), key=lambda x: x[1])
            if timeline
            else None,
            "total_active_days": len(timeline),
        }

    def _extract_key_discussions(
        self, activities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Extract key discussions from activity descriptions."""
        key_discussions = []

        for activity in activities:
            description = activity.get("description", "")
            if (
                description and len(description.strip()) > 50
            ):  # Only include substantial descriptions
                key_discussions.append(
                    {
                        "activity_date": activity.get("activity_date"),
                        "contact_name": activity.get("contact_name"),
                        "specialty": activity.get("specialty"),
                        "subject": activity.get("subject"),
                        "description": description.strip(),
                        "priority": activity.get("priority"),
                        "organization": activity.get("contact_account_name"),
                    }
                )

        # Sort by date (most recent first) and limit to top discussions
        key_discussions.sort(key=lambda x: x.get("activity_date", ""), reverse=True)
        return key_discussions[:20]  # Top 20 discussions

    def _analyze_priority_distribution(
        self, activities: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze priority distribution across activities."""
        priority_counts = defaultdict(int)
        priority_by_specialty = defaultdict(lambda: defaultdict(int))

        for activity in activities:
            priority = activity.get("priority", "Unknown")
            specialty = activity.get("specialty", "Unknown")

            priority_counts[priority] += 1
            priority_by_specialty[specialty][priority] += 1

        return {
            "overall_distribution": dict(priority_counts),
            "by_specialty": dict(priority_by_specialty),
            "high_priority_percentage": round(
                (priority_counts["High"] / max(sum(priority_counts.values()), 1)) * 100,
                1,
            ),
        }

    def _analyze_recent_trends(
        self, activities: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze recent activity trends."""
        from datetime import datetime, timedelta

        now = datetime.now().date()
        last_week = now - timedelta(days=7)
        last_two_weeks = now - timedelta(days=14)

        recent_activities = []
        previous_week_activities = []

        for activity in activities:
            activity_date_str = activity.get("activity_date")
            if activity_date_str:
                try:
                    # Handle different date formats
                    if isinstance(activity_date_str, str):
                        activity_date = datetime.fromisoformat(
                            activity_date_str.replace("Z", "+00:00")
                        ).date()
                    elif isinstance(activity_date_str, date):
                        activity_date = activity_date_str
                    else:
                        activity_date = datetime.fromisoformat(
                            str(activity_date_str)
                        ).date()

                    if activity_date >= last_week:
                        recent_activities.append(activity)
                    elif activity_date >= last_two_weeks:
                        previous_week_activities.append(activity)
                except (ValueError, AttributeError, TypeError):
                    continue

        return {
            "last_week_count": len(recent_activities),
            "previous_week_count": len(previous_week_activities),
            "week_over_week_change": len(recent_activities)
            - len(previous_week_activities),
            "recent_specialties": list(
                set(
                    activity.get("specialty", "Unknown")
                    for activity in recent_activities
                )
            ),
            "trend_direction": "up"
            if len(recent_activities) > len(previous_week_activities)
            else "down",
        }

    def _calculate_date_range_days(self, start_date_str: str, end_date_str: str) -> int:
        """Calculate the number of days in the date range."""
        try:
            # Handle different date formats
            if isinstance(start_date_str, str):
                start_date = datetime.fromisoformat(
                    start_date_str.replace("Z", "+00:00")
                ).date()
            elif isinstance(start_date_str, date):
                start_date = start_date_str
            else:
                start_date = datetime.fromisoformat(str(start_date_str)).date()

            if isinstance(end_date_str, str):
                end_date = datetime.fromisoformat(
                    end_date_str.replace("Z", "+00:00")
                ).date()
            elif isinstance(end_date_str, date):
                end_date = end_date_str
            else:
                end_date = datetime.fromisoformat(str(end_date_str)).date()

            return (end_date - start_date).days + 1
        except (ValueError, AttributeError, TypeError) as e:
            self.logger.warning(
                f"Error calculating date range: {e}, using default value"
            )
            return 0
