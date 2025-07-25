#!/usr/bin/env python3
"""
Analyze the lunch scheduling email thread
"""

import os
import sys
import json
from datetime import datetime

# Add the app directory to Python path
app_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, app_dir)

from dotenv import load_dotenv
load_dotenv()

from database.session import db_session
from database.data_models.email_data import Email
from sqlalchemy import or_


def analyze_lunch_thread():
    """Analyze the lunch scheduling email thread"""
    for session in db_session():
        # Find emails related to lunch scheduling
        lunch_emails = session.query(Email).filter(
            or_(
                Email.subject.ilike('%lunch%'),
                Email.subject.ilike('%ortho%')
            )
        ).order_by(Email.date.desc()).all()
        
        print(f"\nFound {len(lunch_emails)} emails related to lunch scheduling")
        print("=" * 80)
        
        for i, email in enumerate(lunch_emails, 1):
            # Convert Unix timestamp to readable date
            email_date = datetime.fromtimestamp(email.date)
            
            print(f"\n{'='*80}")
            print(f"EMAIL #{i}")
            print(f"{'='*80}")
            
            # Basic metadata
            print(f"\n[METADATA]")
            print(f"Subject: {email.subject}")
            print(f"From: {email.from_email} ({email.from_name or 'No name'})")
            print(f"Date: {email_date.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Thread ID: {email.thread_id}")
            print(f"Nylas ID: {email.nylas_id}")
            
            # Recipients
            print(f"\n[RECIPIENTS]")
            if email.to_emails:
                print(f"To: {json.dumps(email.to_emails, indent=2)}")
            if email.cc_emails:
                print(f"CC: {json.dumps(email.cc_emails, indent=2)}")
            
            # Content preview
            print(f"\n[CONTENT PREVIEW]")
            print(f"Snippet: {email.snippet}")
            
            # Full body (first 1000 chars)
            if email.body:
                print(f"\n[BODY - First 1000 chars]")
                print(email.body[:1000])
                if len(email.body) > 1000:
                    print(f"\n... (truncated, total length: {len(email.body)} chars)")
            
            # Plain text body if available
            if email.body_plain:
                print(f"\n[PLAIN TEXT BODY - First 500 chars]")
                print(email.body_plain[:500])
                if len(email.body_plain) > 500:
                    print(f"\n... (truncated, total length: {len(email.body_plain)} chars)")
            
            # Processing status
            print(f"\n[STATUS]")
            print(f"Unread: {email.unread}")
            print(f"Processed: {email.processed}")
            print(f"Processing Status: {email.processing_status}")
            
            # Raw webhook data structure (if available)
            if email.raw_webhook_data:
                print(f"\n[RAW WEBHOOK DATA KEYS]")
                if isinstance(email.raw_webhook_data, dict):
                    for key in email.raw_webhook_data.keys():
                        print(f"  - {key}")
        
        # Analyze thread structure
        print(f"\n\n{'='*80}")
        print("THREAD ANALYSIS")
        print(f"{'='*80}")
        
        # Group by thread ID
        thread_groups = {}
        for email in lunch_emails:
            if email.thread_id not in thread_groups:
                thread_groups[email.thread_id] = []
            thread_groups[email.thread_id].append(email)
        
        print(f"\nFound {len(thread_groups)} unique threads:")
        for thread_id, emails in thread_groups.items():
            print(f"\nThread: {thread_id}")
            print(f"  Messages: {len(emails)}")
            for email in sorted(emails, key=lambda x: x.date):
                email_date = datetime.fromtimestamp(email.date)
                print(f"    - {email_date.strftime('%Y-%m-%d %H:%M')} | {email.from_email} | {email.subject[:50]}")
        
        break


if __name__ == "__main__":
    analyze_lunch_thread()