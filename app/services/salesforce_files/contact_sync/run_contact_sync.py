#!/usr/bin/env python3
"""
Salesforce Contact Sync CLI

This script provides a command-line interface for syncing Salesforce contacts
using either the Bulk API or REST API approaches.
"""

import sys
import os
import argparse
import logging
from datetime import datetime, timedelta
from typing import Optional

# Add the project root to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
)
if project_root not in sys.path:
    sys.path.append(project_root)

from app.database.session import SessionLocal
from app.services.salesforce_files.contact_sync.bulk_contact_sync_service import (
    BulkContactSyncService,
)
from app.services.salesforce_files.contact_sync.sf_contact_sync_service import (
    SfContactSyncService,
)
from app.services.salesforce_files.bulk_salesforce_service import BulkSalesforceService
from app.services.salesforce_files.salesforce_service import ReadOnlySalesforceService

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("contact_sync.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def run_bulk_sync(modified_since: Optional[datetime] = None, batch_size: int = 1000):
    """Run contact sync using the Bulk API."""
    logger.info("Starting Bulk API contact sync...")

    db_session = None
    try:
        # Initialize services
        sf_bulk_service = BulkSalesforceService()
        db_session = SessionLocal()
        sync_service = BulkContactSyncService(db_session, sf_bulk_service)

        # Get initial count
        from app.database.data_models.salesforce_data import SfContact

        initial_count = db_session.query(SfContact).count()
        logger.info(f"Initial contacts in database: {initial_count:,}")

        # Run sync
        stats = sync_service.bulk_sync_contacts(modified_since, batch_size)

        # Get final count
        final_count = db_session.query(SfContact).count()

        # Log results
        logger.info("Bulk sync completed successfully!")
        logger.info("Final Statistics:")
        logger.info(f"Total retrieved: {stats['total_retrieved']:,}")
        logger.info(f"Total processed: {stats['total_processed']:,}")
        logger.info(f"New records: {stats['new_records']:,}")
        logger.info(f"Updated records: {stats['updated_records']:,}")
        logger.info(f"Errors: {stats['errors']:,}")
        logger.info(f"Final database count: {final_count:,}")

        return True

    except Exception as e:
        logger.error(f"Bulk sync failed: {str(e)}")
        return False
    finally:
        if db_session:
            db_session.close()


def run_rest_sync(
    modified_since: Optional[datetime] = None, limit: Optional[int] = None
):
    """Run contact sync using the REST API."""
    logger.info("Starting REST API contact sync...")

    db_session = None
    try:
        # Initialize services
        sf_service = ReadOnlySalesforceService()
        db_session = SessionLocal()
        sync_service = SfContactSyncService(db_session, sf_service)

        # Get initial count
        from app.database.data_models.salesforce_data import SfContact

        initial_count = db_session.query(SfContact).count()
        logger.info(f"Initial contacts in database: {initial_count:,}")

        # Run sync
        synced_contacts = sync_service.sync_contacts(modified_since, limit)

        # Get final count
        final_count = db_session.query(SfContact).count()

        # Log results
        logger.info("REST sync completed successfully!")
        logger.info(f"Contacts synced: {len(synced_contacts):,}")
        logger.info(f"Final database count: {final_count:,}")

        return True

    except Exception as e:
        logger.error(f"REST sync failed: {str(e)}")
        return False
    finally:
        if db_session:
            db_session.close()


def test_connections():
    """Test both Bulk API and REST API connections."""
    logger.info("Testing API connections...")

    # Test Bulk API
    try:
        sf_bulk_service = BulkSalesforceService()
        if sf_bulk_service.authenticate():
            logger.info("✅ Bulk API connection successful")
        else:
            logger.error("❌ Bulk API connection failed")
            return False
    except Exception as e:
        logger.error(f"❌ Bulk API test failed: {str(e)}")
        return False

    # Test REST API
    try:
        sf_service = ReadOnlySalesforceService()
        # Simple test query
        result = sf_service.query("SELECT Id FROM Contact LIMIT 1")
        if result:
            logger.info("✅ REST API connection successful")
        else:
            logger.error("❌ REST API connection failed")
            return False
    except Exception as e:
        logger.error(f"❌ REST API test failed: {str(e)}")
        return False

    logger.info("✅ All API connections successful!")
    return True


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Salesforce Contact Sync CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test connections
  python run_contact_sync.py --test
  
  # Full sync using Bulk API
  python run_contact_sync.py --mode bulk --full
  
  # Incremental sync using Bulk API (last 7 days)
  python run_contact_sync.py --mode bulk --days 7
  
  # REST API sync with limit
  python run_contact_sync.py --mode rest --limit 1000
  
  # Custom date range using Bulk API
  python run_contact_sync.py --mode bulk --start-date 2024-01-01
        """,
    )

    parser.add_argument(
        "--mode",
        choices=["bulk", "rest"],
        default="bulk",
        help="API mode to use (default: bulk)",
    )

    parser.add_argument("--test", action="store_true", help="Test API connections only")

    parser.add_argument("--full", action="store_true", help="Sync all contacts")

    parser.add_argument(
        "--days", type=int, help="Sync contacts modified in the last N days"
    )

    parser.add_argument(
        "--start-date",
        type=str,
        help="Sync contacts modified since this date (YYYY-MM-DD)",
    )

    parser.add_argument(
        "--limit", type=int, help="Limit number of records to sync (REST API only)"
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=1000,
        help="Batch size for processing (Bulk API only, default: 1000)",
    )

    args = parser.parse_args()

    # Test mode
    if args.test:
        success = test_connections()
        sys.exit(0 if success else 1)

    # Determine modified_since date
    modified_since = None
    if args.days:
        modified_since = datetime.now() - timedelta(days=args.days)
        logger.info(f"Syncing contacts modified since: {modified_since}")
    elif args.start_date:
        try:
            modified_since = datetime.fromisoformat(args.start_date)
            logger.info(f"Syncing contacts modified since: {modified_since}")
        except ValueError:
            logger.error("Invalid date format. Use YYYY-MM-DD")
            sys.exit(1)
    elif not args.full:
        # Default to last 7 days if no specific option is provided
        modified_since = datetime.now() - timedelta(days=7)
        logger.info(
            f"No specific date range provided. Defaulting to last 7 days: {modified_since}"
        )

    # Run sync based on mode
    try:
        if args.mode == "bulk":
            success = run_bulk_sync(modified_since, args.batch_size)
        else:  # rest
            success = run_rest_sync(modified_since, args.limit)

        if success:
            logger.info("✅ Contact sync completed successfully!")
            sys.exit(0)
        else:
            logger.error("❌ Contact sync failed!")
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("Sync interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
