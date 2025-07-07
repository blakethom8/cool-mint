from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
import os
from dotenv import load_dotenv
from app.services.salesforce_files.salesforce_monitoring import SalesforceMonitoring
from app.services.salesforce_files.salesforce_service import (
    ReadOnlySalesforceService,
    SalesforceConfig,
)

load_dotenv()


class RestActivityService:
    """Service class for read-only Salesforce activity operations.

    This class provides specialized methods for reading Task and Event data from Salesforce,
    while ensuring no write operations can occur.
    """

    def __init__(self, config: Optional[SalesforceConfig] = None):
        """Initialize the REST activity service using the base ReadOnlySalesforceService."""
        # Use the existing ReadOnlySalesforceService as our base
        self._sf_service = ReadOnlySalesforceService(config)
        self.monitoring = self._sf_service.monitoring

    def get_tasks_query(
        self, modified_since: Optional[datetime] = None, offset: int = 0
    ) -> str:
        """Build the SOQL query for Task data."""
        fields = [
            # Standard Fields
            "Id",
            "WhoCount",
            "WhatCount",
            "Subject",
            "ActivityDate",
            "Status",
            "Priority",
            "IsHighPriority",
            "Description",
            "IsDeleted",
            "IsClosed",
            "IsArchived",
            "TaskSubtype",
            "CompletedDateTime",
            # Custom Fields
            "MNO_Subtype_c__c",
            "MNO_Primary_Attendees_ID__c",
            "MNO_Type__c",
            "MN_Tags__c",
            "MNO_Setting__c",
            "Attendees_Concatenation__c",
            "Comments_Short__c",
            # Relationship Fields
            "WhoId",
            "WhatId",
            "OwnerId",
            "AccountId",
            "CreatedById",
            "LastModifiedById",
            # System Fields
            "CreatedDate",
            "LastModifiedDate",
            "SystemModstamp",
            # Additional fields for reference
            "Account.Name",
            "Who.Name",
            "Who.Type",
            "What.Name",
            "What.Type",
        ]

        where_clause = ""
        if modified_since:
            where_clause = f"WHERE LastModifiedDate >= {modified_since.isoformat()}Z"

        return f"""
            SELECT {", ".join(fields)}
            FROM Task
            {where_clause}
            ORDER BY LastModifiedDate DESC
            LIMIT 200 OFFSET {offset}
        """

    def get_events_query(
        self, modified_since: Optional[datetime] = None, offset: int = 0
    ) -> str:
        """Build the SOQL query for Event data."""
        fields = [
            # Standard Fields from Task
            "Id",
            "WhoCount",
            "WhatCount",
            "Subject",
            "ActivityDate",
            "Description",
            "IsDeleted",
            "IsArchived",
            # Event-specific Fields
            "StartDateTime",
            "EndDateTime",
            "DurationInMinutes",
            "Location",
            "ShowAs",
            "IsAllDayEvent",
            "IsPrivate",
            "IsRecurrence",
            "IsReminderSet",
            "ReminderDateTime",
            # Custom Fields (if applicable to events)
            "MNO_Type__c",
            "MN_Tags__c",
            "MNO_Setting__c",
            "Attendees_Concatenation__c",
            # Relationship Fields
            "WhoId",
            "WhatId",
            "OwnerId",
            "AccountId",
            "CreatedById",
            "LastModifiedById",
            # System Fields
            "CreatedDate",
            "LastModifiedDate",
            "SystemModstamp",
            # Additional fields for reference
            "Account.Name",
            "Who.Name",
            "Who.Type",
            "What.Name",
            "What.Type",
        ]

        where_clause = ""
        if modified_since:
            where_clause = f"WHERE LastModifiedDate >= {modified_since.isoformat()}Z"

        return f"""
            SELECT {", ".join(fields)}
            FROM Event
            {where_clause}
            ORDER BY LastModifiedDate DESC
            LIMIT 200 OFFSET {offset}
        """

    def _get_paginated_results(
        self,
        query_builder,
        modified_since: Optional[datetime] = None,
        batch_size: int = 200,
    ) -> List[Dict[str, Any]]:
        """
        Helper method to handle paginated queries.

        Args:
            query_builder: Function that builds the SOQL query
            modified_since: Optional datetime filter
            batch_size: Number of records per page

        Returns:
            List of all records across all pages
        """
        all_records = []
        offset = 0

        while True:
            query = query_builder(modified_since=modified_since, offset=offset)
            batch = self._sf_service.query(query)

            if not batch:  # No more records
                break

            all_records.extend(batch)

            if len(batch) < batch_size:  # Last page
                break

            offset += batch_size

        return all_records

    def get_tasks(
        self, modified_since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve all tasks from Salesforce using pagination."""
        return self._get_paginated_results(
            query_builder=self.get_tasks_query, modified_since=modified_since
        )

    def get_events(
        self, modified_since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve all events from Salesforce using pagination."""
        return self._get_paginated_results(
            query_builder=self.get_events_query, modified_since=modified_since
        )

    def get_activity_by_id(
        self, activity_type: str, activity_id: str
    ) -> Dict[str, Any]:
        """Retrieve a specific activity by its ID.

        Args:
            activity_type: Either 'Task' or 'Event'
            activity_id: Salesforce ID of the activity
        """
        if activity_type not in ["Task", "Event"]:
            raise ValueError("activity_type must be either 'Task' or 'Event'")

        # Use the appropriate query based on type
        if activity_type == "Task":
            query = self.get_tasks_query()
        else:
            query = self.get_events_query()

        # Add ID filter
        query = query.replace("ORDER BY", f"WHERE Id = '{activity_id}' ORDER BY")
        results = self._sf_service.query(query)
        return results[0] if results else {}

    def get_api_limits(self) -> Dict[str, Any]:
        """Get current API usage and limits."""
        return self._sf_service.get_api_limits()

    def get_usage_report(self, date: str = None) -> Dict[str, Any]:
        """Get API usage report for a specific date."""
        return self._sf_service.get_usage_report(date)
