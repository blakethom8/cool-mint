from datetime import datetime, timedelta
import logging
from typing import Optional, Literal
from sqlalchemy.orm import Session
import argparse

from app.database.session import db_session
from app.services.salesforce_files.taskwhorelation_sync.taskwhorelation_sync_service import (
    TaskWhoRelationSyncService,
)
from app.services.salesforce_files.taskwhorelation_sync.rest_taskwhorelation_service import (
    RestTaskWhoRelationService,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("taskwhorelation_sync.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def get_date_range(
    sync_mode: Literal["full", "recent", "custom"] = "recent",
    days_back: Optional[int] = 30,
    start_date: Optional[datetime] = None,
) -> Optional[datetime]:
    """
    Get the modified_since date based on sync mode.

    Args:
        sync_mode:
            - "full": Sync all TaskWhoRelation records (returns None)
            - "recent": Sync records from last N days
            - "custom": Sync records since specific date
        days_back: Number of days to look back for recent mode
        start_date: Specific start date for custom mode

    Returns:
        datetime or None if full sync
    """
    if sync_mode == "full":
        return None
    elif sync_mode == "recent":
        return datetime.now() - timedelta(days=days_back)
    elif sync_mode == "custom":
        return start_date
    else:
        raise ValueError(f"Invalid sync_mode: {sync_mode}")


def run_taskwhorelation_sync(
    db_session: Session,
    sync_mode: Literal["full", "recent", "custom"] = "recent",
    days_back: Optional[int] = 30,
    start_date: Optional[datetime] = None,
    limit: Optional[int] = None,
) -> None:
    """
    Run the TaskWhoRelation sync process to sync Salesforce TaskWhoRelation records to local database.

    Args:
        db_session: SQLAlchemy database session
        sync_mode: Type of sync to perform ("full", "recent", or "custom")
        days_back: For recent mode, number of days to look back
        start_date: For custom mode, specific start date
        limit: Optional limit on number of records to sync
    """
    try:
        logger.info(f"Starting TaskWhoRelation sync at {datetime.now()}")
        logger.info(f"Sync mode: {sync_mode}")

        modified_since = get_date_range(sync_mode, days_back, start_date)

        if modified_since:
            logger.info(
                f"Syncing TaskWhoRelation records modified since: {modified_since}"
            )
        else:
            logger.info("Performing full sync of all TaskWhoRelation records")

        # Initialize services
        rest_service = RestTaskWhoRelationService()
        sync_service = TaskWhoRelationSyncService(db_session, rest_service)

        # Check API limits before starting
        api_limits = rest_service.get_api_limits()
        logger.info(
            f"Current API usage: {api_limits.get('used', 0)}/{api_limits.get('total', 0)}"
        )

        # Run sync
        stats = sync_service.sync_taskwhorelations(
            modified_since, limit, sync_mode=sync_mode
        )

        # Log final results
        logger.info("TaskWhoRelation sync completed successfully!")
        logger.info("Final Statistics:")
        logger.info(f"Total records retrieved: {stats['total_retrieved']:,}")
        logger.info(f"Total records processed: {stats['total_processed']:,}")
        logger.info(f"Total successful: {stats['total_successful']:,}")
        logger.info(f"Total failed: {stats['total_failed']:,}")
        logger.info(f"Batches processed: {stats['batches_processed']:,}")

        if stats["total_processed"] > 0:
            success_rate = (stats["total_successful"] / stats["total_processed"]) * 100
            logger.info(f"Success rate: {success_rate:.2f}%")

        if stats.get("sync_results_file"):
            logger.info(f"Detailed results saved to: {stats['sync_results_file']}")

        # Check final API usage
        final_limits = rest_service.get_api_limits()
        logger.info(
            f"Final API usage: {final_limits.get('used', 0)}/{final_limits.get('total', 0)}"
        )

    except Exception as e:
        logger.error(f"Error during TaskWhoRelation sync: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Sync Salesforce TaskWhoRelation records"
    )
    parser.add_argument(
        "--mode",
        choices=["full", "recent", "custom"],
        default="recent",
        help="Sync mode: full (all records), recent (last N days), or custom (since specific date)",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Number of days to look back for recent mode",
    )
    parser.add_argument(
        "--start-date",
        type=str,
        help="Start date for custom mode (format: YYYY-MM-DD)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Optional limit on number of records to sync",
    )

    args = parser.parse_args()

    # Parse custom start date if provided
    custom_start_date = None
    if args.start_date:
        try:
            custom_start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
        except ValueError as e:
            logger.error(f"Invalid start date format. Use YYYY-MM-DD. Error: {e}")
            exit(1)

    # Get database session
    session_generator = db_session()
    session = next(session_generator)

    try:
        run_taskwhorelation_sync(
            session,
            sync_mode=args.mode,
            days_back=args.days,
            start_date=custom_start_date,
            limit=args.limit,
        )
    except Exception as e:
        logger.error(f"Failed to run TaskWhoRelation sync: {str(e)}", exc_info=True)
        raise
    finally:
        try:
            next(session_generator)  # This will trigger the commit
        except StopIteration:
            pass  # Expected when generator is exhausted
