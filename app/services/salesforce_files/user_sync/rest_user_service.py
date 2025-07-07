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


class RestUserService:
    """Service class for read-only Salesforce user operations.

    This class provides specialized methods for reading User data from Salesforce,
    while ensuring no write operations can occur.
    """

    def __init__(self, config: Optional[SalesforceConfig] = None):
        """Initialize the REST user service using the base ReadOnlySalesforceService."""
        self._sf_service = ReadOnlySalesforceService(config)
        self.monitoring = self._sf_service.monitoring

    def get_users_query(
        self, modified_since: Optional[datetime] = None, offset: int = 0
    ) -> str:
        """Build the SOQL query for User data."""
        fields = [
            # Required Fields
            "Id",
            "Username",
            "LastName",
            "Name",
            "Email",
            "IsProfilePhotoActive",
            "CreatedDate",
            "LastModifiedDate",
            "SystemModstamp",
            # Optional Fields
            "FirstName",
            "MiddleName",
            "Suffix",
            # Address Fields (will be stored as JSONB)
            "Street",
            "City",
            "State",
            "PostalCode",
            "Country",
            "Latitude",
            "Longitude",
            # Custom Fields
            "External_ID__c",
        ]

        where_clause = ""
        if modified_since:
            where_clause = f"WHERE LastModifiedDate >= {modified_since.isoformat()}Z"

        return f"""
            SELECT {", ".join(fields)}
            FROM User
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

    def get_users(
        self, modified_since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve all users from Salesforce using pagination."""
        return self._get_paginated_results(
            query_builder=self.get_users_query, modified_since=modified_since
        )

    def get_user_by_id(self, user_id: str) -> Dict[str, Any]:
        """Retrieve a specific user by their ID.

        Args:
            user_id: Salesforce ID of the user
        """
        query = self.get_users_query()
        query = query.replace("ORDER BY", f"WHERE Id = '{user_id}' ORDER BY")
        results = self._sf_service.query(query)
        return results[0] if results else {}

    def get_api_limits(self) -> Dict[str, Any]:
        """Get current API usage and limits."""
        return self._sf_service.get_api_limits()

    def get_usage_report(self, date: str = None) -> Dict[str, Any]:
        """Get API usage report for a specific date."""
        return self._sf_service.get_usage_report(date)
