"""
Monthly Activity Summary Analyzer

This analyzer handles the complex relationship between Activities and Contacts
through the TaskWhoRelation table, properly aggregating multiple contacts per activity.
"""

from typing import Dict, List, Any, Type, Optional
from pydantic import BaseModel, Field
from datetime import datetime, date
from collections import defaultdict

from .base_analyzer import BaseAnalyzer


class ActivityContactInfo(BaseModel):
    """Schema for contact information within an activity."""

    contact_id: str
    contact_name: str
    specialty: Optional[str] = None
    title: Optional[str] = None
    organization: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    is_physician: bool = False
    provider_type: Optional[str] = None
    employment_status: Optional[str] = None
    mailing_city: Optional[str] = None
    mn_mgma_specialty: Optional[str] = None
    mn_primary_geography: Optional[str] = None
    mn_specialty_group: Optional[str] = None


class ActivityInfo(BaseModel):
    """Schema for activity information."""

    activity_id: str
    activity_date: str
    subject: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    mno_type: Optional[str] = None
    mno_subtype: Optional[str] = None
    mn_tags: Optional[str] = None
    comments_short: Optional[str] = None
    contacts: List[ActivityContactInfo] = Field(default_factory=list)


class MonthlyActivitySummaryOutput(BaseModel):
    """Output schema for monthly activity summary analysis."""

    summary_period: Dict[str, Any]
    basic_metrics: Dict[str, Any]
    activities: List[ActivityInfo]
    specialty_distribution: Dict[str, int]
    contact_distribution: Dict[str, int]
    organization_distribution: Dict[str, int]


class MonthlyActivitySummaryAnalyzer(BaseAnalyzer):
    """
    Analyzer for monthly activity summaries with proper handling of multiple contacts per activity.

    This analyzer:
    1. Properly joins Activities with Contacts through TaskWhoRelation
    2. Aggregates multiple contacts per activity using JSON functions
    3. Structures data for comprehensive LLM analysis
    """

    @property
    def analyzer_name(self) -> str:
        return "monthly_activity_summary"

    @property
    def description(self) -> str:
        return "Analyzes monthly activity data with complete contact relationships through TaskWhoRelation table"

    def get_sql_query(self) -> str:
        """
        SQL query that properly handles multiple contacts per activity.

        Uses JSON aggregation to collect all contacts for each activity.
        """
        return """
        SELECT 
            -- Activity information
            a.id as activity_id,
            a.salesforce_id as activity_sf_id,
            a.activity_date,
            a.subject,
            a.description,
            a.status,
            a.priority,
            a.mno_type,
            a.mno_subtype,
            a.mn_tags,
            a.comments_short,
            
            -- Aggregated contact information as JSON
            COALESCE(
                JSON_AGG(
                    JSON_BUILD_OBJECT(
                        'contact_id', c.salesforce_id,
                        'contact_name', c.name,
                        'specialty', c.specialty,
                        'title', c.title,
                        'organization', c.contact_account_name,
                        'email', c.email,
                        'phone', c.phone,
                        'is_physician', c.is_physician,
                        'provider_type', c.provider_type,
                        'employment_status', c.employment_status_mn,
                        'mailing_city', c.mailing_city,
                        'mn_mgma_specialty', c.mn_mgma_specialty,
                        'mn_primary_geography', c.mn_primary_geography,
                        'mn_specialty_group', c.mn_specialty_group
                    )
                ) FILTER (WHERE c.id IS NOT NULL),
                '[]'::json
            ) as contacts
            
        FROM sf_activities a
        LEFT JOIN sf_taskwhorelations twr ON a.salesforce_id = twr.task_id AND twr.is_deleted = false
        LEFT JOIN sf_contacts c ON twr.relation_id = c.salesforce_id
        WHERE a.owner_id = :user_id
          AND a.activity_date >= :start_date
          AND a.activity_date <= :end_date
          AND a.description IS NOT NULL
          AND a.description != ''
          AND a.is_deleted = false
        GROUP BY 
            a.id, a.salesforce_id, a.activity_date, a.subject, a.description,
            a.status, a.priority, a.mno_type, a.mno_subtype, a.mn_tags, a.comments_short
        ORDER BY a.activity_date DESC, a.sf_created_date DESC
        """

    def structure_data(
        self, raw_data: List[Dict[str, Any]], query_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Structure raw SQL data for LLM consumption.

        Args:
            raw_data: Raw results from SQL query
            query_params: Parameters used in the query

        Returns:
            Structured data ready for LLM analysis
        """
        # Process activities with their contacts
        activities = []
        specialty_counts = defaultdict(int)
        contact_counts = defaultdict(int)
        organization_counts = defaultdict(int)

        for row in raw_data:
            # Parse contacts JSON
            contacts_json = row.get("contacts", [])
            if isinstance(contacts_json, str):
                import json

                try:
                    contacts_json = json.loads(contacts_json)
                except json.JSONDecodeError:
                    contacts_json = []

            # Create contact info objects
            contacts = []
            for contact_data in contacts_json:
                if contact_data and contact_data.get("contact_id"):
                    contacts.append(ActivityContactInfo(**contact_data))

                    # Count specialties
                    specialty = contact_data.get("specialty", "Unknown")
                    specialty_counts[specialty] += 1

                    # Count contacts
                    contact_name = contact_data.get("contact_name", "Unknown")
                    contact_counts[contact_name] += 1

                    # Count organizations
                    organization = contact_data.get("organization", "Unknown")
                    organization_counts[organization] += 1

            # Create activity info
            activity = ActivityInfo(
                activity_id=row.get("activity_id", ""),
                activity_date=row.get("activity_date", ""),
                subject=row.get("subject", ""),
                description=row.get("description", ""),
                status=row.get("status", ""),
                priority=row.get("priority", ""),
                mno_type=row.get("mno_type", ""),
                mno_subtype=row.get("mno_subtype", ""),
                mn_tags=row.get("mn_tags", ""),
                comments_short=row.get("comments_short", ""),
                contacts=contacts,
            )
            activities.append(activity)

        # Create summary period information
        summary_period = {
            "start_date": str(query_params.get("start_date", "")),
            "end_date": str(query_params.get("end_date", "")),
            "user_id": query_params.get("user_id", ""),
            "total_activities": len(activities),
            "total_days": self._calculate_date_range_days(
                query_params.get("start_date"), query_params.get("end_date")
            ),
        }

        # Create basic metrics
        basic_metrics = {
            "total_activities": len(activities),
            "unique_contacts": len(contact_counts),
            "unique_organizations": len(organization_counts),
            "unique_specialties": len(specialty_counts),
            "date_range": f"{query_params.get('start_date')} to {query_params.get('end_date')}",
            "activities_with_contacts": sum(1 for a in activities if a.contacts),
            "activities_without_contacts": sum(1 for a in activities if not a.contacts),
            "total_contact_relationships": sum(len(a.contacts) for a in activities),
        }

        # Convert to dictionaries for JSON serialization
        activities_dict = [activity.model_dump() for activity in activities]

        # Create structured data
        structured_data = {
            "summary_period": summary_period,
            "basic_metrics": basic_metrics,
            "activities": activities_dict,
            "specialty_distribution": dict(
                sorted(specialty_counts.items(), key=lambda x: x[1], reverse=True)
            ),
            "contact_distribution": dict(
                sorted(contact_counts.items(), key=lambda x: x[1], reverse=True)
            ),
            "organization_distribution": dict(
                sorted(organization_counts.items(), key=lambda x: x[1], reverse=True)
            ),
        }

        return structured_data

    def get_output_schema(self) -> Type[BaseModel]:
        """Return the output schema for validation."""
        return MonthlyActivitySummaryOutput

    def _calculate_date_range_days(self, start_date, end_date) -> int:
        """Calculate the number of days in the date range."""
        try:
            if isinstance(start_date, str):
                start_date = datetime.fromisoformat(
                    start_date.replace("Z", "+00:00")
                ).date()
            elif isinstance(start_date, date):
                pass
            else:
                start_date = datetime.fromisoformat(str(start_date)).date()

            if isinstance(end_date, str):
                end_date = datetime.fromisoformat(
                    end_date.replace("Z", "+00:00")
                ).date()
            elif isinstance(end_date, date):
                pass
            else:
                end_date = datetime.fromisoformat(str(end_date)).date()

            return (end_date - start_date).days + 1
        except (ValueError, AttributeError, TypeError) as e:
            self.logger.warning(
                f"Error calculating date range: {e}, using default value"
            )
            return 0

    def get_required_parameters(self) -> List[str]:
        """Return the required parameters for this analyzer."""
        return ["user_id", "start_date", "end_date"]

    def export_debug_data(
        self, structured_data: Dict[str, Any], export_path: str
    ) -> None:
        """
        Export structured data with additional debug information.

        Args:
            structured_data: Data to export
            export_path: Path to export the data to
        """
        # Add debug-specific information
        debug_data = structured_data.copy()
        debug_data["_debug_info"] = {
            "analyzer": self.analyzer_name,
            "description": self.description,
            "export_timestamp": datetime.now().isoformat(),
            "sample_activity_with_contacts": self._get_sample_activity_with_contacts(
                structured_data
            ),
            "contact_relationship_stats": self._get_contact_relationship_stats(
                structured_data
            ),
        }

        # Use parent's export method
        super().export_debug_data(debug_data, export_path)

    def _get_sample_activity_with_contacts(
        self, structured_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get a sample activity that has contacts for debugging."""
        activities = structured_data.get("activities", [])
        for activity in activities:
            if activity.get("contacts"):
                return {
                    "activity_id": activity.get("activity_id"),
                    "subject": activity.get("subject"),
                    "contact_count": len(activity.get("contacts", [])),
                    "contact_names": [
                        c.get("contact_name") for c in activity.get("contacts", [])
                    ],
                    "specialties": [
                        c.get("specialty") for c in activity.get("contacts", [])
                    ],
                }
        return {}

    def _get_contact_relationship_stats(
        self, structured_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get statistics about contact relationships."""
        activities = structured_data.get("activities", [])

        contact_counts = []
        for activity in activities:
            contact_counts.append(len(activity.get("contacts", [])))

        return {
            "total_activities": len(activities),
            "activities_with_contacts": sum(1 for count in contact_counts if count > 0),
            "activities_without_contacts": sum(
                1 for count in contact_counts if count == 0
            ),
            "max_contacts_per_activity": max(contact_counts) if contact_counts else 0,
            "avg_contacts_per_activity": sum(contact_counts) / len(contact_counts)
            if contact_counts
            else 0,
            "total_contact_relationships": sum(contact_counts),
        }
