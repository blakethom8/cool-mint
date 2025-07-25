import os
import sys
from dotenv import load_dotenv

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

from database.session import db_session
from services.nylas_email_service import NylasEmailService
from database.data_models.email_data import Email


def test_email_sync():
    """Test syncing recent emails from Nylas"""
    print("Testing email sync...")
    print("-" * 50)
    
    grant_id = os.environ.get("NYLAS_GRANT_ID")
    if not grant_id:
        print("Error: NYLAS_GRANT_ID not found in environment")
        return
    
    # Get a database session
    for session in db_session():
        # Initialize email service
        email_service = NylasEmailService(session)
        
        # Check existing emails in database
        existing_count = session.query(Email).count()
        print(f"Existing emails in database: {existing_count}")
        
        # Sync recent emails
        print("\nSyncing recent emails from Nylas...")
        synced_emails = email_service.sync_recent_emails(grant_id, limit=10)
        
        print(f"\nSynced {len(synced_emails)} new emails:")
        for email in synced_emails:
            print(f"  - {email.subject[:50]}... (from: {email.from_email})")
        
        # Show total count
        total_count = session.query(Email).count()
        print(f"\nTotal emails in database: {total_count}")
        
        # Show some recent emails
        print("\nRecent emails in database:")
        recent_emails = session.query(Email).order_by(Email.date.desc()).limit(5).all()
        for email in recent_emails:
            print(f"  - {email.subject[:50]}...")
            print(f"    From: {email.from_email}")
            print(f"    Date: {email.date}")
            print(f"    Processed: {email.processed}")
            print(f"    Classification: {email.classification or 'Not classified'}")
            print()
        
        break  # Only use first session


if __name__ == "__main__":
    test_email_sync()