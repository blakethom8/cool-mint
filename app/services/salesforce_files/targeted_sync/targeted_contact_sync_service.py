from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
import logging
import math

from app.database.data_models.salesforce_data import SfContact

try:
    from ..bulk_salesforce_service import BulkSalesforceService
    from ..bulk_contact_sync_service import BulkContactSyncService
    from .rest_salesforce_service import RestSalesforceService
except ImportError:
    # Handle when running directly from the targeted_sync directory
    import sys
    import os

    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, parent_dir)

    from bulk_salesforce_service import BulkSalesforceService
    from bulk_contact_sync_service import BulkContactSyncService
    from rest_salesforce_service import RestSalesforceService

logger = logging.getLogger(__name__)


class TargetedContactSyncService:
    """Service for syncing only contacts that have activities logged against them.

    This service dramatically reduces sync time by focusing on active contacts only,
    using a hybrid approach: REST API for getting contact IDs, Bulk API for contact data.
    """

    def __init__(
        self, db_session: Session, bulk_salesforce_service: BulkSalesforceService
    ):
        self.db = db_session
        self.sf_bulk = bulk_salesforce_service
        # Initialize REST API service for getting contact IDs
        self.sf_rest = RestSalesforceService()
        # Reuse the existing sync logic from BulkContactSyncService
        self.bulk_sync_service = BulkContactSyncService(
            db_session, bulk_salesforce_service
        )

    def get_active_contact_ids(
        self, modified_since: Optional[datetime] = None
    ) -> List[str]:
        """Get unique Contact IDs that have activities logged against them.

        Uses REST API for efficiency with relationship queries.

        Args:
            modified_since: Optional filter for recently modified contacts

        Returns:
            List of Contact IDs from Task.WhoId and Event.WhoId
        """
        try:
            logger.info("🎯 Using hybrid approach: REST API for contact IDs...")

            # Use REST API to get all contact IDs with activities
            contact_ids = self.sf_rest.get_all_contact_ids_with_activities(
                modified_since
            )

            if not contact_ids:
                logger.warning("No active contacts found")
                return []

            logger.info(
                f"✅ Found {len(contact_ids):,} unique contacts with activities"
            )
            return contact_ids

        except Exception as e:
            logger.error(f"Error getting active contact IDs: {str(e)}")
            return []

    def get_targeted_contact_query(
        self, contact_ids: List[str], modified_since: Optional[datetime] = None
    ) -> str:
        """Build the SOQL query for specific Contact IDs.

        Args:
            contact_ids: List of Contact IDs to include
            modified_since: Optional filter for recently modified contacts

        Returns:
            SOQL query string
        """
        # Use the same fields as the bulk sync service
        query = self.bulk_sync_service.get_contact_query(modified_since)

        # Replace the WHERE clause to target specific contacts
        if contact_ids:
            # Convert IDs to quoted strings for SOQL
            quoted_ids = [f"'{id}'" for id in contact_ids]
            ids_clause = ", ".join(quoted_ids)

            # Build targeted WHERE clause
            where_clause = f"WHERE Id IN ({ids_clause}) AND IsDeleted = FALSE"

            # Add time filter if specified
            if modified_since:
                where_clause += (
                    f" AND LastModifiedDate >= {modified_since.isoformat()}Z"
                )

            # Replace the WHERE clause in the base query
            # Find the WHERE clause in the base query and replace it
            query_lines = query.strip().split("\n")
            new_query_lines = []

            for line in query_lines:
                if line.strip().startswith("WHERE"):
                    new_query_lines.append(f"            {where_clause}")
                else:
                    new_query_lines.append(line)

            query = "\n".join(new_query_lines)

        return query

    def sync_contacts_with_activities(
        self,
        modified_since: Optional[datetime] = None,
        batch_size: int = 1000,
    ) -> Dict[str, int]:
        """Sync contacts that have activities logged against them.

        Args:
            modified_since: Only sync contacts modified since this datetime
            batch_size: Number of records to process in each database batch

        Returns:
            Dictionary with sync statistics
        """
        stats = {
            "active_contacts_found": 0,
            "total_retrieved": 0,
            "total_processed": 0,
            "new_records": 0,
            "updated_records": 0,
            "errors": 0,
        }

        try:
            # Step 1: Get active contact IDs
            logger.info("Step 1: Getting contacts with activities...")
            contact_ids = self.get_active_contact_ids(modified_since)

            if not contact_ids:
                logger.warning("No active contacts found, nothing to sync")
                return stats

            stats["active_contacts_found"] = len(contact_ids)
            logger.info(f"Found {len(contact_ids):,} contacts with activities")

            # Step 2: Handle large ID lists by batching
            # Salesforce has limits on IN() clause size (~1000 items)
            max_ids_per_query = 800  # Conservative limit

            if len(contact_ids) > max_ids_per_query:
                logger.info(
                    f"Large dataset detected, will process in batches of {max_ids_per_query} IDs"
                )

                # Process in batches
                for i in range(0, len(contact_ids), max_ids_per_query):
                    batch_ids = contact_ids[i : i + max_ids_per_query]
                    batch_num = (i // max_ids_per_query) + 1
                    total_batches = math.ceil(len(contact_ids) / max_ids_per_query)

                    logger.info(
                        f"Processing ID batch {batch_num}/{total_batches} ({len(batch_ids)} IDs)"
                    )

                    batch_stats = self._sync_contact_batch_by_ids(
                        batch_ids, modified_since, batch_size
                    )

                    # Accumulate stats
                    stats["total_retrieved"] += batch_stats["total_retrieved"]
                    stats["total_processed"] += batch_stats["total_processed"]
                    stats["new_records"] += batch_stats["new_records"]
                    stats["updated_records"] += batch_stats["updated_records"]
                    stats["errors"] += batch_stats["errors"]

                    logger.info(
                        f"Batch {batch_num} completed: {batch_stats['total_processed']} contacts processed"
                    )
            else:
                # Small dataset, process all at once
                logger.info("Processing all contacts in single query")
                batch_stats = self._sync_contact_batch_by_ids(
                    contact_ids, modified_since, batch_size
                )

                # Copy stats
                stats.update(batch_stats)

            logger.info(f"Targeted sync completed: {stats}")
            return stats

        except Exception as e:
            logger.error(f"Error during targeted sync: {str(e)}")
            stats["errors"] += 1
            return stats

    def _sync_contact_batch_by_ids(
        self,
        contact_ids: List[str],
        modified_since: Optional[datetime] = None,
        batch_size: int = 1000,
    ) -> Dict[str, int]:
        """Sync a specific batch of contacts by their IDs.

        Args:
            contact_ids: List of Contact IDs to sync
            modified_since: Optional filter for recently modified contacts
            batch_size: Number of records to process in each database batch

        Returns:
            Dictionary with sync statistics
        """
        stats = {
            "total_retrieved": 0,
            "total_processed": 0,
            "new_records": 0,
            "updated_records": 0,
            "errors": 0,
        }

        try:
            # Build targeted query
            query = self.get_targeted_contact_query(contact_ids, modified_since)

            # Execute bulk query
            logger.info(f"Executing bulk query for {len(contact_ids)} contacts...")
            contacts_data = self.sf_bulk.execute_bulk_query(query, "Contact")

            if not contacts_data:
                logger.warning("No contacts retrieved from Salesforce")
                return stats

            stats["total_retrieved"] = len(contacts_data)
            logger.info(f"Retrieved {len(contacts_data):,} contacts from Salesforce")

            # Process contacts in batches using existing sync logic
            logger.info(f"Processing contacts in batches of {batch_size}")

            for i in range(0, len(contacts_data), batch_size):
                batch = contacts_data[i : i + batch_size]
                batch_stats = self.bulk_sync_service._process_contact_batch(batch)

                # Update overall stats
                stats["total_processed"] += batch_stats["processed"]
                stats["new_records"] += batch_stats["new"]
                stats["updated_records"] += batch_stats["updated"]
                stats["errors"] += batch_stats["errors"]

                logger.info(
                    f"Processed batch {i // batch_size + 1}: {batch_stats['processed']} records"
                )

            return stats

        except Exception as e:
            logger.error(f"Error syncing contact batch: {str(e)}")
            stats["errors"] += len(contact_ids)
            return stats

    def get_activity_statistics(self) -> Dict[str, Any]:
        """Get statistics about activities in the Salesforce org.

        Uses REST API for reliable access to activity data.

        Returns:
            Dictionary with activity statistics
        """
        try:
            logger.info("Getting activity statistics using REST API...")

            # Use REST API to get comprehensive activity statistics
            stats = self.sf_rest.get_activity_counts()

            return {
                "total_tasks": stats.get("total_tasks", 0),
                "total_events": stats.get("total_events", 0),
                "unique_contacts_with_tasks": stats.get(
                    "unique_contacts_with_tasks", 0
                ),
                "unique_contacts_with_events": stats.get(
                    "unique_contacts_with_events", 0
                ),
                "total_activities": stats.get("total_activities", 0),
            }

        except Exception as e:
            logger.error(f"Error getting activity statistics: {str(e)}")
            return {
                "total_tasks": 0,
                "total_events": 0,
                "unique_contacts_with_tasks": 0,
                "unique_contacts_with_events": 0,
                "total_activities": 0,
            }
