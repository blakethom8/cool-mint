#!/usr/bin/env python3
"""
Check detailed information about emails in the database
"""

import os
import sys
from datetime import datetime

# Add the app directory to Python path
app_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, app_dir)

from dotenv import load_dotenv
load_dotenv()

from database.session import db_session
from database.data_models.email_data import Email


def show_email_details():
    """Show detailed information about emails"""
    for session in db_session():
        # Get recent emails
        emails = session.query(Email).order_by(Email.date.desc()).limit(10).all()
        
        print("\nDetailed Email Information")
        print("=" * 80)
        
        for i, email in enumerate(emails, 1):
            # Convert Unix timestamp to readable date
            email_date = datetime.fromtimestamp(email.date)
            
            print(f"\n{i}. {email.subject[:60]}...")
            print(f"   From: {email.from_email} ({email.from_name or 'No name'})")
            print(f"   Date: {email_date.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   Nylas ID: {email.nylas_id}")
            print(f"   Thread ID: {email.thread_id}")
            print(f"   Status: {'🔵 Unread' if email.unread else '⚪ Read'} | {'✅ Processed' if email.processed else '❌ Unprocessed'}")
            print(f"   Classification: {email.classification or 'Not classified'}")
            print(f"   Has Attachments: {'Yes' if email.has_attachments else 'No'}")
            if email.to_emails:
                print(f"   To: {', '.join(email.to_emails[:3])}")
            if email.snippet:
                print(f"   Preview: {email.snippet[:100]}...")
        
        print(f"\n\nTotal emails in database: {session.query(Email).count()}")
        
        # Show sync timeline
        print("\nSync Timeline:")
        sync_times = session.query(Email.created_at).distinct().order_by(Email.created_at.desc()).limit(5).all()
        for sync_time in sync_times:
            print(f"  - {sync_time[0]}")
        
        break


if __name__ == "__main__":
    show_email_details()