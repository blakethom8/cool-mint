#!/usr/bin/env python3
"""
Activity Structuring CLI Tool

Production command-line interface for structuring activity data into
the sf_activities_structured table.

Usage:
    python -m app.cli.structure_activities --help
    python -m app.cli.structure_activities batch --user-id 005UJ000002LyknYAC --days 30
    python -m app.cli.structure_activities rebuild --days 365
    python -m app.cli.structure_activities single --activity-id 00TUJ000003hxyz
"""

import argparse
import sys
import logging
from datetime import datetime, date, timedelta
from typing import Optional

from services.activity_structuring_service import ActivityStructuringService
from database.session import SessionLocal
from database.data_models.salesforce_data import SfActivityStructured


def setup_logging(log_level: str = "INFO"):
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("activity_structuring.log"),
        ],
    )


def structure_single_activity(activity_id: str, debug: bool = False) -> int:
    """
    Structure a single activity.

    Args:
        activity_id: UUID or Salesforce ID of the activity
        debug: Enable debug mode

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Structuring single activity: {activity_id}")

    try:
        service = ActivityStructuringService(debug_mode=debug)
        success = service.structure_activity(activity_id)

        if success:
            logger.info(f"Successfully structured activity: {activity_id}")
            return 0
        else:
            logger.error(f"Failed to structure activity: {activity_id}")
            return 1

    except Exception as e:
        logger.error(f"Error structuring activity {activity_id}: {str(e)}")
        return 1


def structure_batch(
    user_id: str, days: int, batch_size: int = 100, debug: bool = False
) -> int:
    """
    Structure activities in batch for a user.

    Args:
        user_id: Salesforce user ID
        days: Number of days back to process
        batch_size: Batch size for processing
        debug: Enable debug mode

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    logger = logging.getLogger(__name__)

    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    logger.info(f"Batch structuring for user {user_id} from {start_date} to {end_date}")

    try:
        service = ActivityStructuringService(debug_mode=debug)
        results = service.structure_activities_batch(
            user_id, start_date, end_date, batch_size
        )

        logger.info(f"Batch processing complete:")
        logger.info(f"  Total Activities: {results['total_activities']}")
        logger.info(f"  Successful: {results['successful']}")
        logger.info(f"  Failed: {results['failed']}")
        logger.info(f"  Overwritten: {results['overwritten']}")

        if results["errors"]:
            logger.warning(f"  Errors: {len(results['errors'])}")
            for error in results["errors"][:5]:  # Log first 5 errors
                logger.warning(f"    - {error}")

        # Return success if majority succeeded
        if results["successful"] > results["failed"]:
            return 0
        else:
            return 1

    except Exception as e:
        logger.error(f"Error in batch processing: {str(e)}")
        return 1


def rebuild_all_activities(days: int, debug: bool = False) -> int:
    """
    Rebuild all activity structures for the past N days.

    Args:
        days: Number of days back to process
        debug: Enable debug mode

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Rebuilding all activities for the past {days} days")

    try:
        service = ActivityStructuringService(debug_mode=debug)
        results = service.rebuild_all_activities(days)

        logger.info(f"Rebuild complete:")
        logger.info(f"  Users Processed: {results['users_processed']}")
        logger.info(f"  Total Activities: {results['total_activities']}")
        logger.info(f"  Successful: {results['successful']}")
        logger.info(f"  Failed: {results['failed']}")

        if results["errors"]:
            logger.warning(f"  Errors: {len(results['errors'])}")
            for error in results["errors"][:10]:  # Log first 10 errors
                logger.warning(f"    - {error}")

        # Return success if majority succeeded
        if results["successful"] > results["failed"]:
            return 0
        else:
            return 1

    except Exception as e:
        logger.error(f"Error in rebuild: {str(e)}")
        return 1


def get_stats() -> int:
    """
    Get statistics about structured activities.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    logger = logging.getLogger(__name__)

    try:
        db_session = SessionLocal()

        # Basic stats
        total_count = (
            db_session.query(SfActivityStructured)
            .filter(SfActivityStructured.is_current == True)
            .count()
        )

        if total_count == 0:
            logger.info("No structured activities found")
            return 0

        # Contact stats
        multi_contact = (
            db_session.query(SfActivityStructured)
            .filter(
                SfActivityStructured.contact_count > 1,
                SfActivityStructured.is_current == True,
            )
            .count()
        )

        physician_activities = (
            db_session.query(SfActivityStructured)
            .filter(
                SfActivityStructured.activity_has_physicians == True,
                SfActivityStructured.is_current == True,
            )
            .count()
        )

        community_activities = (
            db_session.query(SfActivityStructured)
            .filter(
                SfActivityStructured.activity_has_community == True,
                SfActivityStructured.is_current == True,
            )
            .count()
        )

        logger.info(f"Activity Structuring Statistics:")
        logger.info(f"  Total Structured Activities: {total_count}")
        logger.info(f"  Multi-Contact Activities: {multi_contact}")
        logger.info(f"  Activities with Physicians: {physician_activities}")
        logger.info(f"  Community Activities: {community_activities}")

        # Coverage stats
        coverage_pct = (multi_contact / total_count * 100) if total_count > 0 else 0
        logger.info(f"  Multi-Contact Coverage: {coverage_pct:.1f}%")

        db_session.close()
        return 0

    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        return 1


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Activity Structuring CLI Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Structure activities for a user (last 30 days)
  python -m app.cli.structure_activities batch --user-id 005UJ000002LyknYAC --days 30

  # Rebuild all activities (last 365 days)
  python -m app.cli.structure_activities rebuild --days 365

  # Structure a single activity
  python -m app.cli.structure_activities single --activity-id 00TUJ000003hxyz

  # Get statistics
  python -m app.cli.structure_activities stats
        """,
    )

    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Set logging level (default: INFO)",
    )

    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Single activity command
    single_parser = subparsers.add_parser("single", help="Structure a single activity")
    single_parser.add_argument(
        "--activity-id", required=True, help="Activity ID (UUID or Salesforce ID)"
    )

    # Batch command
    batch_parser = subparsers.add_parser("batch", help="Structure activities in batch")
    batch_parser.add_argument("--user-id", required=True, help="Salesforce user ID")
    batch_parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Number of days back to process (default: 30)",
    )
    batch_parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Batch size for processing (default: 100)",
    )

    # Rebuild command
    rebuild_parser = subparsers.add_parser("rebuild", help="Rebuild all activities")
    rebuild_parser.add_argument(
        "--days",
        type=int,
        default=365,
        help="Number of days back to process (default: 365)",
    )

    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Get statistics")

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)

    if not args.command:
        parser.print_help()
        return 1

    logger.info(f"Starting activity structuring command: {args.command}")

    try:
        if args.command == "single":
            return structure_single_activity(args.activity_id, args.debug)
        elif args.command == "batch":
            return structure_batch(args.user_id, args.days, args.batch_size, args.debug)
        elif args.command == "rebuild":
            return rebuild_all_activities(args.days, args.debug)
        elif args.command == "stats":
            return get_stats()
        else:
            logger.error(f"Unknown command: {args.command}")
            return 1

    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
