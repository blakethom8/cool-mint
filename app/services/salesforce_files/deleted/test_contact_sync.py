import sys
import os
from datetime import datetime

# Add the project root to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
if project_root not in sys.path:
    sys.path.append(project_root)

from app.services.salesforce_files.salesforce_service import ReadOnlySalesforceService
from app.services.salesforce_files.sf_contact_sync_service import SfContactSyncService
from app.database.session import SessionLocal


def test_contact_sync():
    """Test the contact sync process end-to-end."""
    print(f"\nStarting Contact Sync Test at {datetime.now()}")
    print("-" * 60)

    try:
        # Initialize services
        print("1. Initializing services...")
        sf_service = ReadOnlySalesforceService()
        db_session = SessionLocal()
        sync_service = SfContactSyncService(db_session, sf_service)

        # Test 1: Generate and display the query
        print("\n2. Testing query generation...")
        query = sync_service.get_contact_query()
        print(f"Generated query (first 200 chars):")
        print(f"{query[:200]}...")

        # Test 2: Sync a small batch of contacts
        print("\n3. Testing contact sync (limit 5)...")
        try:
            contacts = sync_service.sync_contacts(limit=5)
            print(f"✓ Successfully synced {len(contacts)} contacts")

            # Display sample contact data
            if contacts:
                sample_contact = contacts[0]
                print(f"\nSample contact data:")
                print(f"  Name: {sample_contact.first_name} {sample_contact.last_name}")
                print(f"  Email: {sample_contact.email}")
                print(f"  Specialty: {sample_contact.specialty}")
                print(f"  Is Physician: {sample_contact.is_physician}")
                print(f"  NPI: {sample_contact.npi}")
                print(f"  Salesforce ID: {sample_contact.salesforce_id}")

        except Exception as e:
            print(f"❌ Error during sync: {str(e)}")
            return False

        # Test 3: Check database state
        print("\n4. Checking database state...")
        from app.database.data_models.salesforce_data import SfContact

        total_contacts = db_session.query(SfContact).count()
        print(f"Total contacts in database: {total_contacts}")

        physicians = (
            db_session.query(SfContact).filter(SfContact.is_physician == True).count()
        )
        print(f"Physicians in database: {physicians}")

        with_email = (
            db_session.query(SfContact).filter(SfContact.email.isnot(None)).count()
        )
        print(f"Contacts with email: {with_email}")

        print("\n✓ All tests completed successfully!")
        print("-" * 60)
        return True

    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        print("-" * 60)
        return False

    finally:
        if "db_session" in locals():
            db_session.close()


if __name__ == "__main__":
    success = test_contact_sync()
    sys.exit(0 if success else 1)
