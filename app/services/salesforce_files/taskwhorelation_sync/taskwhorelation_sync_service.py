from datetime import datetime
from typing import Dict, List, Optional
import logging
import json
import os
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert

from app.database.data_models.salesforce_data import SfTaskWhoRelation
from app.services.salesforce_files.taskwhorelation_sync.rest_taskwhorelation_service import (
    RestTaskWhoRelationService,
)

logger = logging.getLogger(__name__)


class TaskWhoRelationSyncService:
    """Service for syncing Salesforce TaskWhoRelation records with local database."""

    def __init__(self, db_session: Session, rest_service: RestTaskWhoRelationService):
        """Initialize the TaskWhoRelation sync service.

        Args:
            db_session: SQLAlchemy database session
            rest_service: REST service for Salesforce TaskWhoRelation operations
        """
        self.db_session = db_session
        self.rest_service = rest_service
        self.sync_results = {
            "successful_records": [],
            "failed_records": [],
            "sync_start_time": None,
            "sync_end_time": None,
            "total_processed": 0,
            "total_successful": 0,
            "total_failed": 0,
            "batches_processed": 0,
        }

    def _transform_taskwhorelation_data(self, sf_relation: Dict) -> Dict:
        """Transform Salesforce TaskWhoRelation data to match our database schema.

        Args:
            sf_relation: Raw Salesforce TaskWhoRelation data

        Returns:
            Transformed TaskWhoRelation data matching our schema
        """
        return {
            "salesforce_id": sf_relation["Id"],
            "is_deleted": sf_relation.get("IsDeleted", False),
            "type": sf_relation.get("Type"),
            "relation_id": sf_relation.get("RelationId"),  # Contact ID
            "task_id": sf_relation.get("TaskId"),
            "created_by_id": sf_relation["CreatedById"],
            "last_modified_by_id": sf_relation["LastModifiedById"],
            "sf_created_date": sf_relation["CreatedDate"],
            "sf_last_modified_date": sf_relation["LastModifiedDate"],
            "sf_system_modstamp": sf_relation["SystemModstamp"],
        }

    def _upsert_single_taskwhorelation(self, relation_data: Dict) -> Dict[str, any]:
        """Upsert a single TaskWhoRelation record into the database.

        Args:
            relation_data: Transformed TaskWhoRelation data

        Returns:
            Dictionary with result status and details
        """
        result = {
            "success": False,
            "salesforce_id": relation_data.get("salesforce_id"),
            "task_id": relation_data.get("task_id"),
            "relation_id": relation_data.get("relation_id"),
            "error": None,
            "action": None,  # 'inserted' or 'updated'
        }

        try:
            stmt = insert(SfTaskWhoRelation).values(relation_data)
            stmt = stmt.on_conflict_do_update(
                constraint="sf_taskwhorelations_salesforce_id_key",
                set_={
                    "is_deleted": stmt.excluded.is_deleted,
                    "type": stmt.excluded.type,
                    "relation_id": stmt.excluded.relation_id,
                    "task_id": stmt.excluded.task_id,
                    "created_by_id": stmt.excluded.created_by_id,
                    "last_modified_by_id": stmt.excluded.last_modified_by_id,
                    "sf_last_modified_date": stmt.excluded.sf_last_modified_date,
                    "sf_system_modstamp": stmt.excluded.sf_system_modstamp,
                },
            )

            db_result = self.db_session.execute(stmt)
            self.db_session.commit()

            result["success"] = True
            result["action"] = "inserted" if db_result.rowcount > 0 else "updated"

        except Exception as e:
            logger.error(
                f"Error upserting TaskWhoRelation {relation_data.get('salesforce_id')}: {str(e)}"
            )
            result["error"] = str(e)
            self.db_session.rollback()

        return result

    def _process_batch(self, relations_data: List[Dict]) -> Dict[str, int]:
        """Process a batch of TaskWhoRelation records individually.

        Args:
            relations_data: List of transformed TaskWhoRelation data

        Returns:
            Dictionary with batch statistics
        """
        batch_stats = {
            "processed": 0,
            "successful": 0,
            "failed": 0,
            "inserted": 0,
            "updated": 0,
        }

        batch_successful = []
        batch_failed = []

        for relation_data in relations_data:
            batch_stats["processed"] += 1
            result = self._upsert_single_taskwhorelation(relation_data)

            if result["success"]:
                batch_stats["successful"] += 1
                if result["action"] == "inserted":
                    batch_stats["inserted"] += 1
                else:
                    batch_stats["updated"] += 1
                batch_successful.append(result)
            else:
                batch_stats["failed"] += 1
                batch_failed.append(result)

        # Add to overall sync results
        self.sync_results["successful_records"].extend(batch_successful)
        self.sync_results["failed_records"].extend(batch_failed)

        return batch_stats

    def _write_sync_results_to_file(self, sync_mode: str) -> str:
        """Write sync results to a markdown file.

        Args:
            sync_mode: The sync mode used (full, recent, custom)

        Returns:
            Path to the created results file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"taskwhorelation_sync_results_{timestamp}.md"
        filepath = os.path.join(os.getcwd(), "sync_results", filename)

        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        with open(filepath, "w") as f:
            f.write(f"# TaskWhoRelation Sync Results\n\n")
            f.write(f"**Sync Mode:** {sync_mode}\n")
            f.write(f"**Start Time:** {self.sync_results['sync_start_time']}\n")
            f.write(f"**End Time:** {self.sync_results['sync_end_time']}\n")
            f.write(
                f"**Duration:** {self.sync_results['sync_end_time'] - self.sync_results['sync_start_time']}\n\n"
            )

            f.write("## Summary Statistics\n\n")
            f.write(f"- **Total Processed:** {self.sync_results['total_processed']}\n")
            f.write(
                f"- **Total Successful:** {self.sync_results['total_successful']}\n"
            )
            f.write(f"- **Total Failed:** {self.sync_results['total_failed']}\n")
            f.write(
                f"- **Batches Processed:** {self.sync_results['batches_processed']}\n"
            )
            f.write(
                f"- **Success Rate:** {(self.sync_results['total_successful'] / self.sync_results['total_processed'] * 100):.2f}%\n\n"
            )

            if self.sync_results["successful_records"]:
                f.write("## Successful Records\n\n")
                f.write("```json\n")
                f.write(
                    json.dumps(
                        self.sync_results["successful_records"], indent=2, default=str
                    )
                )
                f.write("\n```\n\n")

            if self.sync_results["failed_records"]:
                f.write("## Failed Records\n\n")
                f.write("```json\n")
                f.write(
                    json.dumps(
                        self.sync_results["failed_records"], indent=2, default=str
                    )
                )
                f.write("\n```\n\n")

                f.write("### Failed Records Summary\n\n")
                error_types = {}
                for record in self.sync_results["failed_records"]:
                    error_type = type(record.get("error", "Unknown")).__name__
                    error_types[error_type] = error_types.get(error_type, 0) + 1

                for error_type, count in error_types.items():
                    f.write(f"- **{error_type}:** {count} records\n")

        return filepath

    def sync_taskwhorelations(
        self,
        modified_since: Optional[datetime] = None,
        limit: Optional[int] = None,
        sync_mode: str = "unknown",
    ) -> Dict[str, int]:
        """Sync TaskWhoRelation records from Salesforce to local database.

        Args:
            modified_since: Only sync records modified after this datetime
            limit: Optional limit on number of records to sync
            sync_mode: The sync mode being used (for logging)

        Returns:
            Dictionary with sync statistics
        """
        self.sync_results["sync_start_time"] = datetime.now()

        stats = {
            "total_retrieved": 0,
            "total_processed": 0,
            "total_successful": 0,
            "total_failed": 0,
            "batches_processed": 0,
            "sync_results_file": None,
        }

        try:
            # Fetch TaskWhoRelation records from Salesforce
            relations = self.rest_service.get_taskwhorelations(modified_since)

            if limit:
                relations = relations[:limit]

            stats["total_retrieved"] = len(relations)

            if not relations:
                logger.info("No TaskWhoRelation records found to sync")
                return stats

            # Process records in batches
            batch_size = 200
            for i in range(0, len(relations), batch_size):
                batch = relations[i : i + batch_size]
                batch_number = (i // batch_size) + 1

                logger.info(
                    f"Processing batch {batch_number} of {(len(relations) + batch_size - 1) // batch_size} ({len(batch)} records)"
                )

                transformed_batch = [
                    self._transform_taskwhorelation_data(relation) for relation in batch
                ]

                batch_stats = self._process_batch(transformed_batch)

                # Update overall stats
                stats["total_processed"] += batch_stats["processed"]
                stats["total_successful"] += batch_stats["successful"]
                stats["total_failed"] += batch_stats["failed"]
                stats["batches_processed"] += 1

                logger.info(
                    f"Batch {batch_number} completed: {batch_stats['successful']} successful, {batch_stats['failed']} failed"
                )

            # Update sync results
            self.sync_results["sync_end_time"] = datetime.now()
            self.sync_results["total_processed"] = stats["total_processed"]
            self.sync_results["total_successful"] = stats["total_successful"]
            self.sync_results["total_failed"] = stats["total_failed"]
            self.sync_results["batches_processed"] = stats["batches_processed"]

            # Write results to file
            results_file = self._write_sync_results_to_file(sync_mode)
            stats["sync_results_file"] = results_file
            logger.info(f"Sync results written to: {results_file}")

        except Exception as e:
            logger.error(f"Error during TaskWhoRelation sync: {str(e)}", exc_info=True)
            stats["total_failed"] += 1

        return stats
