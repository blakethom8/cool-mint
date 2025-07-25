#!/usr/bin/env python3
"""
Simple Email Sync Script (No Celery Dependencies)

This script syncs emails without queueing them for processing.
Perfect for development and testing.
"""

import os
import sys
import argparse
from datetime import datetime, timedelta

# Add the app directory to Python path
app_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, app_dir)

from dotenv import load_dotenv
load_dotenv()

from database.session import db_session
from services.nylas_email_service import NylasEmailService
from database.data_models.email_data import Email


def sync_recent_emails(minutes_back=30, limit=50):
    """Sync recent emails from Nylas"""
    grant_id = os.environ.get("NYLAS_GRANT_ID")
    if not grant_id:
        print("Error: NYLAS_GRANT_ID not found in environment")
        return
    
    print(f"\nSyncing emails from last {minutes_back} minutes...")
    print("=" * 70)
    
    # Calculate timestamp
    since_timestamp = int((datetime.utcnow() - timedelta(minutes=minutes_back)).timestamp())
    
    # Get database session
    for session in db_session():
        email_service = NylasEmailService(session)
        
        # Get current email count
        before_count = session.query(Email).count()
        
        # Sync emails
        try:
            from nylas import Client
            client = Client(
                api_key=os.environ.get("NYLAS_API_KEY"),
                api_uri=os.environ.get("NYLAS_API_URI"),
            )
            
            # Fetch recent messages
            query_params = {
                "limit": limit,
                "received_after": since_timestamp
            }
            
            messages = client.messages.list(grant_id, query_params)
            message_list = messages[0] if isinstance(messages, tuple) else messages
            
            print(f"Found {len(message_list)} messages from Nylas")
            
            new_count = 0
            updated_count = 0
            
            for message in message_list:
                # Check if email exists
                existing = session.query(Email).filter_by(
                    nylas_id=message.id
                ).first()
                
                if existing:
                    # Update existing email
                    existing.unread = message.unread
                    existing.starred = message.starred
                    existing.updated_at = datetime.utcnow()
                    updated_count += 1
                else:
                    # Create new email
                    email = email_service._create_email_from_message(message, grant_id)
                    if email:
                        new_count += 1
            
            session.commit()
            
            # Show results
            after_count = session.query(Email).count()
            print(f"\nSync Results:")
            print(f"  New emails: {new_count}")
            print(f"  Updated emails: {updated_count}")
            print(f"  Total emails in DB: {after_count}")
            
            # Show some recent emails
            if new_count > 0:
                print(f"\nRecent emails:")
                recent = session.query(Email).order_by(
                    Email.date.desc()
                ).limit(5).all()
                
                for email in recent:
                    status = "🔵" if email.unread else "⚪"
                    processed = "✓" if email.processed else "✗"
                    print(f"  {status} {email.subject[:50]}...")
                    print(f"     From: {email.from_email}")
                    print(f"     Processed: {processed}")
            
        except Exception as e:
            print(f"Error syncing emails: {e}")
            session.rollback()
        
        break  # Exit after first session


def show_status():
    """Show email sync status"""
    print("\nEmail Database Status")
    print("=" * 70)
    
    for session in db_session():
        total = session.query(Email).count()
        unread = session.query(Email).filter(Email.unread == True).count()
        unprocessed = session.query(Email).filter(Email.processed == False).count()
        
        print(f"Total emails: {total}")
        print(f"Unread emails: {unread}")
        print(f"Unprocessed emails: {unprocessed}")
        
        # Show classification breakdown
        print("\nEmail Classifications:")
        classifications = session.query(
            Email.classification,
            session.query(Email).filter(Email.classification == Email.classification).count()
        ).group_by(Email.classification).all()
        
        for classification, count in classifications:
            print(f"  {classification or 'Not classified'}: {count}")
        
        # Show recent activity
        latest = session.query(Email).order_by(Email.created_at.desc()).first()
        if latest:
            print(f"\nLast sync: {latest.created_at}")
        
        break


def main():
    parser = argparse.ArgumentParser(description="Simple email sync tool")
    parser.add_argument(
        "--minutes",
        type=int,
        default=30,
        help="Minutes to look back (default: 30)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Max emails to sync (default: 50)"
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show status and exit"
    )
    
    args = parser.parse_args()
    
    if args.status:
        show_status()
    else:
        sync_recent_emails(args.minutes, args.limit)


if __name__ == "__main__":
    main()