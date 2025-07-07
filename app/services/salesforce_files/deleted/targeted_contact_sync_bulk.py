#!/usr/bin/env python3
"""
Targeted Contact Sync for Salesforce - Active Contacts Only

This script syncs only contacts that have activities logged against them,
dramatically reducing sync time by focusing on active contacts.
"""

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
from app.services.salesforce_files.targeted_contact_sync_service import (
    TargetedContactSyncService,
)
from app.database.session import SessionLocal

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("targeted_contact_sync.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


def get_active_contact_ids_count():
    """Get a count of contacts with activities (for estimation purposes)."""
    start_time = datetime.now()
    logger.info("Getting count of contacts with activities using REST API...")

    try:
        from app.services.salesforce_files.rest_salesforce_service import (
            RestSalesforceService,
        )

        rest_service = RestSalesforceService()

        if not rest_service.authenticate():
            logger.error("Failed to authenticate with Salesforce REST API")
            return 0

        # Get activity statistics
        logger.info("Getting activity statistics...")
        stats = rest_service.get_activity_counts()

        # Get unique contacts from TaskWhoRelation
        unique_contacts = stats.get("unique_contacts_with_activities", 0)
        total_relations = stats.get("total_task_relations", 0)
        unique_tasks = stats.get("unique_tasks", 0)

        logger.info(f"📊 TaskWhoRelation Summary:")
        logger.info(f"  - Total Task-Contact Relations: {total_relations:,}")
        logger.info(f"  - Unique Contacts with Activities: {unique_contacts:,}")
        logger.info(f"  - Unique Tasks: {unique_tasks:,}")

        return unique_contacts

    except Exception as e:
        logger.error(f"Error getting contact count: {str(e)}")
        return 0


def sync_active_contacts_only():
    """Sync only contacts that have activities logged against them."""
    start_time = datetime.now()
    logger.info(f"Starting TARGETED contact sync at {start_time}")
    logger.info("=" * 80)
    logger.info("Syncing ONLY contacts with logged activities")
    logger.info("=" * 80)

    db_session = None
    try:
        # Get count estimate first
        estimated_count = get_active_contact_ids_count()
        if estimated_count > 0:
            logger.info(f"📊 Estimated contacts to sync: {estimated_count:,}")
            estimated_time = (estimated_count / 3000) * 60  # ~3000 contacts/minute
            logger.info(f"⏱️  Estimated sync time: {estimated_time:.1f} minutes")
        else:
            logger.warning("Could not get count estimate, proceeding anyway...")

        # Initialize services
        logger.info("Initializing targeted sync services...")
        sf_bulk_service = BulkSalesforceService()
        db_session = SessionLocal()
        targeted_sync_service = TargetedContactSyncService(db_session, sf_bulk_service)

        # Get initial database state
        from app.database.data_models.salesforce_data import SfContact

        initial_count = db_session.query(SfContact).count()
        logger.info(f"Initial contacts in database: {initial_count:,}")

        # Execute targeted sync
        logger.info("Starting targeted contact sync...")
        logger.info("Step 1: Getting contacts with activities...")

        stats = targeted_sync_service.sync_contacts_with_activities(
            batch_size=1000,  # Process in batches of 1000
        )

        # Get final database state
        final_count = db_session.query(SfContact).count()

        # Calculate final statistics
        end_time = datetime.now()
        duration = end_time - start_time

        # Log comprehensive results
        logger.info("=" * 80)
        logger.info("TARGETED SYNC COMPLETED SUCCESSFULLY!")
        logger.info("=" * 80)
        logger.info(f"Duration: {duration}")
        logger.info(f"Active contacts found: {stats['active_contacts_found']:,}")
        logger.info(f"Contacts retrieved from Salesforce: {stats['total_retrieved']:,}")
        logger.info(f"Contacts processed: {stats['total_processed']:,}")
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
        logger.info(f"  🎯 Active contacts synced: {stats['total_processed']:,}")
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

        # Efficiency metrics
        if estimated_count > 0:
            efficiency = (stats["total_processed"] / estimated_count) * 100
            logger.info(
                f"  🎯 Sync efficiency: {efficiency:.1f}% of estimated contacts"
            )

        logger.info("=" * 80)

        return True

    except Exception as e:
        logger.error(f"Targeted sync failed with error: {str(e)}")
        logger.exception("Full error details:")
        return False

    finally:
        if db_session:
            db_session.close()
            logger.info("Database session closed")


def incremental_sync_active_contacts(days_back: int = 7):
    """Perform incremental sync of active contacts modified in the last N days."""
    start_time = datetime.now()
    modified_since = start_time - timedelta(days=days_back)

    logger.info(f"Starting INCREMENTAL targeted contact sync at {start_time}")
    logger.info(f"Syncing active contacts modified since: {modified_since}")
    logger.info("=" * 80)

    db_session = None
    try:
        # Initialize services
        logger.info("Initializing targeted sync services...")
        sf_bulk_service = BulkSalesforceService()
        db_session = SessionLocal()
        targeted_sync_service = TargetedContactSyncService(db_session, sf_bulk_service)

        # Execute incremental sync
        stats = targeted_sync_service.sync_contacts_with_activities(
            modified_since=modified_since,
            batch_size=500,  # Smaller batches for incremental sync
        )

        # Log results
        end_time = datetime.now()
        duration = end_time - start_time

        logger.info("=" * 80)
        logger.info("INCREMENTAL TARGETED SYNC COMPLETED!")
        logger.info("=" * 80)
        logger.info(f"Duration: {duration}")
        logger.info(f"Active contacts found: {stats['active_contacts_found']:,}")
        logger.info(f"Contacts retrieved: {stats['total_retrieved']:,}")
        logger.info(f"Contacts processed: {stats['total_processed']:,}")
        logger.info(f"New contacts: {stats['new_records']:,}")
        logger.info(f"Updated contacts: {stats['updated_records']:,}")
        logger.info(f"Errors: {stats['errors']:,}")

        return True

    except Exception as e:
        logger.error(f"Incremental targeted sync failed with error: {str(e)}")
        logger.exception("Full error details:")
        return False

    finally:
        if db_session:
            db_session.close()
            logger.info("Database session closed")


def test_targeted_connection():
    """Test the targeted sync connection and get sample data."""
    logger.info("Testing hybrid targeted sync connection...")

    try:
        from app.services.salesforce_files.rest_salesforce_service import (
            RestSalesforceService,
        )

        # Test REST API
        rest_service = RestSalesforceService()

        # Test REST API authentication
        if rest_service.test_connection():
            logger.info("✅ REST API authentication successful!")

            # Test getting contact IDs with activities
            logger.info("Testing contact ID retrieval...")

            # Get a small sample of contact IDs
            task_contacts = rest_service.get_contact_ids_with_activities()[
                :5
            ]  # Just first 5

            if task_contacts:
                logger.info(f"✅ Found sample contact IDs: {task_contacts}")

                # Test Bulk API with these specific IDs
                logger.info("Testing Bulk API with specific contact IDs...")
                sf_bulk_service = BulkSalesforceService()

                if sf_bulk_service.authenticate():
                    contact_test_query = f"""
                        SELECT Id, FirstName, LastName, Email 
                        FROM Contact 
                        WHERE Id IN ('{task_contacts[0]}', '{task_contacts[1]}')
                        AND IsDeleted = FALSE
                    """

                    logger.info("Testing targeted contact query...")
                    contact_results = sf_bulk_service.execute_bulk_query(
                        contact_test_query, "Contact"
                    )

                    if contact_results:
                        logger.info(
                            f"✅ Hybrid approach successful! Retrieved {len(contact_results)} contacts from {len(task_contacts)} IDs"
                        )
                        logger.info("🎯 Hybrid sync approach is working properly!")
                        return True
                    else:
                        logger.error("❌ Bulk API contact query failed")
                        return False
                else:
                    logger.error("❌ Bulk API authentication failed")
                    return False
            else:
                logger.error("❌ No contact IDs found with activities")
                return False
        else:
            logger.error("❌ REST API authentication failed")
            return False

    except Exception as e:
        logger.error(f"❌ Targeted sync test failed: {str(e)}")
        return False


def main():
    """Main function to run the targeted sync."""
    logger.info("🎯 SALESFORCE TARGETED CONTACT SYNC")
    logger.info("=" * 80)
    logger.info("This script syncs ONLY contacts with logged activities,")
    logger.info("dramatically reducing sync time and focusing on active contacts.")
    logger.info("=" * 80)

    # Parse command line arguments
    import argparse

    parser = argparse.ArgumentParser(description="Salesforce Targeted Contact Sync")
    parser.add_argument(
        "--test", action="store_true", help="Test targeted sync connection only"
    )
    parser.add_argument(
        "--count", action="store_true", help="Get count of contacts with activities"
    )
    parser.add_argument(
        "--incremental",
        type=int,
        metavar="DAYS",
        help="Perform incremental sync for active contacts modified in last N days",
    )
    parser.add_argument(
        "--full", action="store_true", help="Perform full sync of all active contacts"
    )

    args = parser.parse_args()

    # Default to full sync if no arguments provided
    if not any([args.test, args.count, args.incremental, args.full]):
        args.full = True

    success = False

    try:
        if args.test:
            success = test_targeted_connection()
        elif args.count:
            count = get_active_contact_ids_count()
            success = count > 0
        elif args.incremental:
            success = incremental_sync_active_contacts(args.incremental)
        elif args.full:
            success = sync_active_contacts_only()

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
