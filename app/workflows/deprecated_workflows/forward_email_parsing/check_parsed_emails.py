#!/usr/bin/env python3
"""
Check parsed emails in the database
"""

import os
import sys
import json
from datetime import datetime

# Add the app directory to Python path
app_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, app_dir)

from dotenv import load_dotenv
load_dotenv()

from database.session import db_session
from database.data_models.email_data import Email  # Import for relationship
from database.data_models.email_parsed_data import EmailParsed


def check_parsed_emails():
    """Display parsed emails from the database"""
    
    for session in db_session():
        # Get recent parsed emails
        parsed_emails = session.query(EmailParsed).order_by(
            EmailParsed.parsed_at.desc()
        ).limit(5).all()
        
        print("\nParsed Emails in Database")
        print("=" * 80)
        
        for i, parsed in enumerate(parsed_emails, 1):
            print(f"\n{i}. Parsed Email ID: {parsed.id}")
            print(f"   Original Email ID: {parsed.email_id}")
            print(f"   Parsed At: {parsed.parsed_at}")
            print(f"   Model Used: {parsed.model_used}")
            
            print(f"\n   Classification:")
            print(f"   - Type: {parsed.email_type}")
            print(f"   - Is Forwarded: {parsed.is_forwarded}")
            print(f"   - Action Required: {parsed.is_action_required}")
            
            if parsed.user_request:
                print(f"\n   User Request:")
                print(f"   {parsed.user_request[:100]}...")
                print(f"   Intents: {parsed.request_intents}")
            
            if parsed.people:
                print(f"\n   People Extracted: {len(parsed.people)}")
                for person in parsed.people[:3]:
                    print(f"   - {person.get('name')} ({person.get('role', 'N/A')})")
            
            if parsed.meeting_info:
                print(f"\n   Meeting Info:")
                print(f"   - Type: {parsed.meeting_info.get('type')}")
                print(f"   - Topics: {parsed.meeting_info.get('topics', [])[:2]}")
            
            if parsed.action_items:
                print(f"\n   Action Items: {len(parsed.action_items)}")
                for item in parsed.action_items[:2]:
                    print(f"   - {item.get('task')[:60]}...")
            
            print("\n" + "-" * 80)
        
        print(f"\nTotal parsed emails: {session.query(EmailParsed).count()}")
        break


if __name__ == "__main__":
    check_parsed_emails()