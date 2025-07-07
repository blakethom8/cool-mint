import sys
import os
from datetime import datetime, timedelta
import logging

# Add the project root to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
if project_root not in sys.path:
    sys.path.append(project_root)

from app.services.salesforce_files.bulk_salesforce_service import BulkSalesforceService
from app.services.salesforce_files.bulk_contact_sync_service import (
    BulkContactSyncService,
)
from app.database.session import SessionLocal

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("bulk_contact_sync.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def bulk_sync_all_contacts():
    """Bulk sync all contacts from Salesforce to the local database using Bulk API."""
    start_time = datetime.now()
    logger.info(f"Starting BULK contact sync at {start_time}")
    logger.info("=" * 80)

    db_session = None
    try:
        # Initialize services
        logger.info("Initializing bulk services...")
        sf_bulk_service = BulkSalesforceService()
        db_session = SessionLocal()
        bulk_sync_service = BulkContactSyncService(db_session, sf_bulk_service)

        # Get initial database state
        from app.database.data_models.salesforce_data import SfContact

        initial_count = db_session.query(SfContact).count()
        logger.info(f"Initial contacts in database: {initial_count:,}")

        # Execute bulk sync
        logger.info("Starting bulk contact sync...")
        logger.info("This may take several minutes for large datasets...")

        stats = bulk_sync_service.bulk_sync_contacts(
            modified_since=None,  # Sync all contacts
            batch_size=1000,  # Process in batches of 1000
        )

        # Get final database state
        final_count = db_session.query(SfContact).count()

        # Calculate final statistics
        end_time = datetime.now()
        duration = end_time - start_time

        # Log comprehensive results
        logger.info("=" * 80)
        logger.info("BULK SYNC COMPLETED SUCCESSFULLY!")
        logger.info("=" * 80)
        logger.info(f"Duration: {duration}")
        logger.info(
            f"Total contacts retrieved from Salesforce: {stats['total_retrieved']:,}"
        )
        logger.info(f"Total contacts processed: {stats['total_processed']:,}")
        logger.info(f"New contacts added: {stats['new_records']:,}")
        logger.info(f"Existing contacts updated: {stats['updated_records']:,}")
        logger.info(f"Errors encountered: {stats['errors']:,}")
        logger.info(f"Final database count: {final_count:,}")

        # Additional statistics
        physicians = (
            db_session.query(SfContact).filter(SfContact.is_physician == True).count()
        )
        with_email = (
            db_session.query(SfContact).filter(SfContact.email.isnot(None)).count()
        )
        with_npi = db_session.query(SfContact).filter(SfContact.npi.isnot(None)).count()
        active_contacts = (
            db_session.query(SfContact).filter(SfContact.active == True).count()
        )

        logger.info("=" * 80)
        logger.info("DATABASE STATISTICS:")
        logger.info(f"  📊 Total contacts: {final_count:,}")
        logger.info(f"  👨‍⚕️ Physicians: {physicians:,}")
        logger.info(f"  📧 Contacts with email: {with_email:,}")
        logger.info(f"  🆔 Contacts with NPI: {with_npi:,}")
        logger.info(f"  ✅ Active contacts: {active_contacts:,}")

        # Performance metrics
        if duration.total_seconds() > 0:
            records_per_second = stats["total_processed"] / duration.total_seconds()
            logger.info(
                f"  ⚡ Processing rate: {records_per_second:.1f} records/second"
            )

        logger.info("=" * 80)

        return True

    except Exception as e:
        logger.error(f"Bulk sync failed with error: {str(e)}")
        logger.exception("Full error details:")
        return False

    finally:
        if db_session:
            db_session.close()
            logger.info("Database session closed")


def incremental_sync_contacts(days_back: int = 7):
    """Perform incremental sync of contacts modified in the last N days.

    Args:
        days_back: Number of days to look back for modified contacts
    """
    start_time = datetime.now()
    modified_since = start_time - timedelta(days=days_back)

    logger.info(f"Starting INCREMENTAL contact sync at {start_time}")
    logger.info(f"Syncing contacts modified since: {modified_since}")
    logger.info("=" * 80)

    db_session = None
    try:
        # Initialize services
        logger.info("Initializing bulk services...")
        sf_bulk_service = BulkSalesforceService()
        db_session = SessionLocal()
        bulk_sync_service = BulkContactSyncService(db_session, sf_bulk_service)

        # Execute incremental sync
        stats = bulk_sync_service.bulk_sync_contacts(
            modified_since=modified_since,
            batch_size=500,  # Smaller batches for incremental sync
        )

        # Log results
        end_time = datetime.now()
        duration = end_time - start_time

        logger.info("=" * 80)
        logger.info("INCREMENTAL SYNC COMPLETED!")
        logger.info("=" * 80)
        logger.info(f"Duration: {duration}")
        logger.info(f"Contacts retrieved: {stats['total_retrieved']:,}")
        logger.info(f"Contacts processed: {stats['total_processed']:,}")
        logger.info(f"New contacts: {stats['new_records']:,}")
        logger.info(f"Updated contacts: {stats['updated_records']:,}")
        logger.info(f"Errors: {stats['errors']:,}")

        return True

    except Exception as e:
        logger.error(f"Incremental sync failed with error: {str(e)}")
        logger.exception("Full error details:")
        return False

    finally:
        if db_session:
            db_session.close()
            logger.info("Database session closed")


def test_bulk_connection():
    """Test the bulk API connection and authentication."""
    logger.info("Testing Bulk API connection...")

    try:
        sf_bulk_service = BulkSalesforceService()

        # Test authentication
        if sf_bulk_service.authenticate():
            logger.info("✅ Bulk API authentication successful!")

            # Test a small query
            test_query = """
                SELECT Id, FirstName, LastName, Email 
                FROM Contact 
                WHERE IsDeleted = FALSE 
                LIMIT 10
            """

            logger.info("Testing small bulk query...")
            results = sf_bulk_service.execute_bulk_query(test_query)

            if results:
                logger.info(
                    f"✅ Test query successful! Retrieved {len(results)} sample records"
                )
                return True
            else:
                logger.error("❌ Test query failed - no results returned")
                return False
        else:
            logger.error("❌ Bulk API authentication failed")
            return False

    except Exception as e:
        logger.error(f"❌ Bulk API test failed: {str(e)}")
        return False


def main():
    """Main function to run the bulk sync."""
    logger.info("🚀 SALESFORCE BULK CONTACT SYNC")
    logger.info("=" * 80)
    logger.info("This script uses the Salesforce Bulk API to efficiently")
    logger.info("extract large volumes of contact data.")
    logger.info("=" * 80)

    # Parse command line arguments
    import argparse

    parser = argparse.ArgumentParser(description="Salesforce Bulk Contact Sync")
    parser.add_argument(
        "--test", action="store_true", help="Test bulk API connection only"
    )
    parser.add_argument(
        "--incremental",
        type=int,
        metavar="DAYS",
        help="Perform incremental sync for contacts modified in last N days",
    )
    parser.add_argument(
        "--full", action="store_true", help="Perform full sync of all contacts"
    )

    args = parser.parse_args()

    # Default to full sync if no arguments provided
    if not any([args.test, args.incremental, args.full]):
        args.full = True

    success = False

    try:
        if args.test:
            success = test_bulk_connection()
        elif args.incremental:
            success = incremental_sync_contacts(args.incremental)
        elif args.full:
            success = bulk_sync_all_contacts()

        if success:
            logger.info("✅ Operation completed successfully!")
            sys.exit(0)
        else:
            logger.error("❌ Operation failed!")
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("Operation interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        logger.exception("Full error details:")
        sys.exit(1)


if __name__ == "__main__":
    main()
