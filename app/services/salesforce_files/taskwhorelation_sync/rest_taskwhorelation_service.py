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


class RestTaskWhoRelationService:
    """Service class for read-only Salesforce TaskWhoRelation operations.

    This class provides specialized methods for reading TaskWhoRelation data from Salesforce,
    while ensuring no write operations can occur.
    """

    def __init__(self, config: Optional[SalesforceConfig] = None):
        """Initialize the REST TaskWhoRelation service using the base ReadOnlySalesforceService."""
        self._sf_service = ReadOnlySalesforceService(config)
        self.monitoring = self._sf_service.monitoring

    def get_taskwhorelations_query(
        self, modified_since: Optional[datetime] = None, last_id: Optional[str] = None
    ) -> str:
        """Build the SOQL query for TaskWhoRelation data."""
        fields = [
            # Standard Fields
            "Id",
            "IsDeleted",
            "Type",
            # Relationship Fields
            "RelationId",  # References Contact
            "TaskId",  # References Task
            "CreatedById",
            "LastModifiedById",
            # System Fields
            "CreatedDate",
            "LastModifiedDate",
            "SystemModstamp",
            # Additional fields for reference
            "Task.Subject",
            "Task.ActivityDate",
            "Task.Status",
            "Relation.Name",  # Contact name
        ]

        where_clauses = []
        if modified_since:
            where_clauses.append(f"LastModifiedDate >= {modified_since.isoformat()}Z")
        if last_id:
            where_clauses.append(f"Id > '{last_id}'")

        where_clause = " AND ".join(where_clauses)
        if where_clause:
            where_clause = f"WHERE {where_clause}"

        return f"""
            SELECT {", ".join(fields)}
            FROM TaskWhoRelation
            {where_clause}
            ORDER BY Id ASC
            LIMIT 200
        """

    def _get_paginated_results(
        self,
        query_builder,
        modified_since: Optional[datetime] = None,
        batch_size: int = 200,
    ) -> List[Dict[str, Any]]:
        """
        Helper method to handle paginated queries using cursor-based pagination.

        Args:
            query_builder: Function that builds the SOQL query
            modified_since: Optional datetime filter
            batch_size: Number of records per page

        Returns:
            List of all records across all pages
        """
        all_records = []
        last_id = None
        page = 1

        while True:
            try:
                query = query_builder(modified_since=modified_since, last_id=last_id)
                print(f"Fetching page {page} with query: {query}")  # Debug logging

                batch = self._sf_service.query(query)

                if not batch:  # No more records
                    print(f"No more records found after page {page - 1}")
                    break

                records_count = len(batch)
                print(f"Retrieved {records_count} records in page {page}")

                all_records.extend(batch)

                if records_count < batch_size:  # Last page
                    print(f"Last page reached (page {page})")
                    break

                last_id = batch[-1][
                    "Id"
                ]  # Use the last ID as the cursor for the next batch
                page += 1

            except Exception as e:
                print(f"Error fetching page {page}: {str(e)}")
                raise

        print(f"Total records retrieved: {len(all_records)}")
        return all_records

    def get_taskwhorelations(
        self, modified_since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve all TaskWhoRelation records from Salesforce using pagination."""
        return self._get_paginated_results(
            query_builder=self.get_taskwhorelations_query, modified_since=modified_since
        )

    def get_taskwhorelation_by_id(self, relation_id: str) -> Dict[str, Any]:
        """Retrieve a specific TaskWhoRelation by its ID.

        Args:
            relation_id: Salesforce ID of the TaskWhoRelation
        """
        query = self.get_taskwhorelations_query()
        query = query.replace("ORDER BY", f"WHERE Id = '{relation_id}' ORDER BY")
        results = self._sf_service.query(query)
        return results[0] if results else {}

    def get_api_limits(self) -> Dict[str, Any]:
        """Get current API usage and limits."""
        return self._sf_service.get_api_limits()

    def get_usage_report(self, date: str = None) -> Dict[str, Any]:
        """Get API usage report for a specific date."""
        return self._sf_service.get_usage_report(date)
