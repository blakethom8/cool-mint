from datetime import datetime, timedelta
import logging
from typing import Optional, Literal
from sqlalchemy.orm import Session
import argparse

from app.database.session import db_session
from app.services.salesforce_files.activity_sync.activity_sync_service import (
    ActivitySyncService,
)
from app.services.salesforce_files.activity_sync.rest_activity_service import (
    RestActivityService,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("activity_sync.log"), logging.StreamHandler()],
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
            - "full": Sync all activities (returns None)
            - "recent": Sync activities from last N days
            - "custom": Sync activities since specific date
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


def run_activity_sync(
    db_session: Session,
    sync_mode: Literal["full", "recent", "custom"] = "recent",
    days_back: Optional[int] = 30,
    start_date: Optional[datetime] = None,
    limit: Optional[int] = None,
) -> None:
    """
    Run the activity sync process to sync Salesforce Tasks and Events to local database.

    Args:
        db_session: SQLAlchemy database session
        sync_mode: Type of sync to perform ("full", "recent", or "custom")
        days_back: For recent mode, number of days to look back
        start_date: For custom mode, specific start date
        limit: Optional limit on number of records to sync
    """
    try:
        logger.info(f"Starting activity sync at {datetime.now()}")
        logger.info(f"Sync mode: {sync_mode}")

        modified_since = get_date_range(sync_mode, days_back, start_date)

        if modified_since:
            logger.info(f"Syncing activities modified since: {modified_since}")
        else:
            logger.info("Performing full sync of all activities")

        # Initialize services
        rest_service = RestActivityService()
        sync_service = ActivitySyncService(db_session, rest_service)

        # Check API limits before starting
        api_limits = rest_service.get_api_limits()
        logger.info(
            f"Current API usage: {api_limits.get('used', 0)}/{api_limits.get('total', 0)}"
        )

        # Run sync
        stats = sync_service.sync_activities(modified_since, limit)

        # Log final results
        logger.info("Activity sync completed successfully!")
        logger.info("Final Statistics:")
        logger.info(f"Total activities retrieved: {stats['total_retrieved']:,}")
        logger.info(f"Tasks retrieved: {stats['tasks_retrieved']:,}")
        logger.info(f"Events retrieved: {stats['events_retrieved']:,}")
        logger.info(f"New records: {stats['new_records']:,}")
        logger.info(f"Updated records: {stats['updated_records']:,}")
        logger.info(f"Errors: {stats['errors']:,}")

        # Check final API usage
        final_limits = rest_service.get_api_limits()
        logger.info(
            f"Final API usage: {final_limits.get('used', 0)}/{final_limits.get('total', 0)}"
        )

    except Exception as e:
        logger.error(f"Error during activity sync: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sync Salesforce activities")
    parser.add_argument(
        "--mode",
        choices=["full", "recent", "custom"],
        default="recent",
        help="Sync mode: full (all activities), recent (last N days), or custom (since specific date)",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Number of days to look back for recent mode",
    )
    parser.add_argument(
        "--start-date", type=str, help="Start date for custom mode (format: YYYY-MM-DD)"
    )
    parser.add_argument(
        "--limit", type=int, help="Optional limit on number of records to sync"
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
        run_activity_sync(
            session,
            sync_mode=args.mode,
            days_back=args.days,
            start_date=custom_start_date,
            limit=args.limit,
        )
    except Exception as e:
        logger.error(f"Failed to run activity sync: {str(e)}", exc_info=True)
        raise
    finally:
        try:
            next(session_generator)  # This will trigger the commit
        except StopIteration:
            pass  # Expected when generator is exhausted
