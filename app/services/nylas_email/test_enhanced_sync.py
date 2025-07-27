#!/usr/bin/env python3
"""
Test the enhanced email sync with forwarding detection and parsing
"""

import os
import sys
from datetime import datetime, timedelta

# Add the app directory to Python path
app_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, app_dir)

from dotenv import load_dotenv
load_dotenv()

from database.session import db_session
from services.nylas_email_service import NylasEmailService
from database.data_models.email_data import Email
# Import EmailParsed to ensure relationship is loaded
from database.data_models.email_parsed_data import EmailParsed


def test_enhanced_sync():
    """Test syncing emails with enhanced parsing"""
    
    grant_id = os.environ.get("NYLAS_GRANT_ID")
    if not grant_id:
        print("Error: NYLAS_GRANT_ID not found in environment variables")
        return
    
    print(f"Grant ID: {grant_id}")
    
    for session in db_session():
        nylas_service = NylasEmailService(session)
        
        # Sync recent emails
        print("\nSyncing recent emails...")
        synced_emails = nylas_service.sync_recent_emails(grant_id, limit=10)
        
        print(f"\nSynced {len(synced_emails)} emails")
        
        # Check enhanced fields
        for email in synced_emails:
            print(f"\n{'='*80}")
            print(f"Email: {email.subject}")
            print(f"From: {email.from_email}")
            print(f"Date: {datetime.fromtimestamp(email.date)}")
            print(f"Is Forwarded: {email.is_forwarded}")
            
            if email.is_forwarded:
                print(f"\nForwarded Email Detected!")
                if email.user_instruction:
                    print(f"User Instruction: {email.user_instruction[:200]}...")
                if email.extracted_thread:
                    print(f"Extracted Thread: {email.extracted_thread[:200]}...")
            
            if email.clean_body:
                print(f"\nClean Body Preview: {email.clean_body[:200]}...")
            
            if email.message_id:
                print(f"Message ID: {email.message_id}")
            
            print(f"\nConversation for LLM Preview:")
            print(email.conversation_for_llm[:300] + "...")
        
        # Also check existing emails
        print(f"\n{'='*80}")
        print("Checking existing emails for forwarding...")
        
        existing_emails = session.query(Email).filter(
            Email.subject.ilike('%fwd:%')
        ).limit(5).all()
        
        for email in existing_emails:
            print(f"\nEmail: {email.subject}")
            print(f"Is Forwarded (property): {email.is_forwarded_email}")
            print(f"Is Forwarded (field): {email.is_forwarded}")
            print(f"Has User Instruction: {email.has_user_instruction}")
        
        break


if __name__ == "__main__":
    test_enhanced_sync()