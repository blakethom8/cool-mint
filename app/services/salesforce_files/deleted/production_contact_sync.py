import sys
import os
from datetime import datetime
import logging

# Add the project root to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
if project_root not in sys.path:
    sys.path.append(project_root)

from app.services.salesforce_files.salesforce_service import ReadOnlySalesforceService
from app.services.salesforce_files.sf_contact_sync_service import SfContactSyncService
from app.database.session import SessionLocal

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("contact_sync.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def sync_all_contacts():
    """Sync all contacts from Salesforce to the local database."""
    start_time = datetime.now()
    logger.info(f"Starting full contact sync at {start_time}")

    db_session = None
    try:
        # Initialize services
        logger.info("Initializing services...")
        sf_service = ReadOnlySalesforceService()
        db_session = SessionLocal()
        sync_service = SfContactSyncService(db_session, sf_service)

        # Get initial database state
        from app.database.data_models.salesforce_data import SfContact

        initial_count = db_session.query(SfContact).count()
        logger.info(f"Initial contacts in database: {initial_count}")

        # Sync all contacts (no limit)
        logger.info("Starting full contact sync...")
        contacts = sync_service.sync_contacts()  # No limit parameter

        # Get final database state
        final_count = db_session.query(SfContact).count()
        new_contacts = final_count - initial_count

        # Log results
        end_time = datetime.now()
        duration = end_time - start_time

        logger.info(f"Sync completed successfully!")
        logger.info(f"Duration: {duration}")
        logger.info(f"Contacts processed: {len(contacts)}")
        logger.info(f"New contacts added: {new_contacts}")
        logger.info(f"Total contacts in database: {final_count}")

        return True

    except Exception as e:
        logger.error(f"Sync failed with error: {str(e)}")
        logger.exception("Full error details:")
        return False

    finally:
        if db_session:
            db_session.close()
            logger.info("Database session closed")


def main():
    """Main function to run the sync."""
    logger.info("=" * 60)
    logger.info("PRODUCTION CONTACT SYNC")
    logger.info("=" * 60)

    success = sync_all_contacts()

    if success:
        logger.info("✓ Contact sync completed successfully")
        sys.exit(0)
    else:
        logger.error("❌ Contact sync failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
