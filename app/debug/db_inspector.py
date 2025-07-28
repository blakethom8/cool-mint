#!/usr/bin/env python3
"""
Database State Inspector
Utility to inspect and monitor database state for debugging
"""
import os
import sys
from datetime import datetime, timedelta
from typing import Optional, List
import argparse

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from database.session import db_session
from database.data_models.email_data import Email, EmailAttachment, EmailActivity
from database.data_models.email_actions import EmailAction, CallLogStaging, NoteStaging, ReminderStaging
from database.event import Event
from sqlalchemy import desc, func


class DatabaseInspector:
    """Inspect database state for debugging"""
    
    def __init__(self):
        self.db = next(db_session())
    
    def __del__(self):
        if hasattr(self, 'db'):
            self.db.close()
    
    def inspect_emails(self, limit: int = 10, show_all: bool = False):
        """Inspect email records"""
        print("\n" + "=" * 80)
        print("📧 EMAIL RECORDS")
        print("=" * 80)
        
        # Get total counts
        total = self.db.query(Email).count()
        processed = self.db.query(Email).filter(Email.processed == True).count()
        unprocessed = self.db.query(Email).filter(Email.processed == False).count()
        
        print(f"\n📊 Statistics:")
        print(f"   Total emails: {total}")
        print(f"   Processed: {processed}")
        print(f"   Unprocessed: {unprocessed}")
        
        # Get recent emails
        query = self.db.query(Email).order_by(desc(Email.date))
        if not show_all:
            query = query.limit(limit)
        
        emails = query.all()
        
        print(f"\n📋 Recent Emails (showing {len(emails)}):")
        print("-" * 80)
        
        for email in emails:
            # Convert timestamp to datetime
            email_date = datetime.fromtimestamp(email.date) if email.date else None
            
            print(f"\n📧 Email ID: {email.id}")
            print(f"   Subject: {email.subject}")
            print(f"   From: {email.from_email} ({email.from_name})")
            print(f"   To: {email.to_emails}")
            print(f"   Date: {email_date}")
            print(f"   Processed: {'✅' if email.processed else '❌'} ({email.processing_status})")
            print(f"   Forwarded: {'Yes' if email.is_forwarded else 'No'}")
            print(f"   Has Body: {'Yes' if email.body else 'No'}")
            print(f"   User Instruction: {email.user_instruction[:50] + '...' if email.user_instruction else 'None'}")
            
            # Check for related actions
            actions = self.db.query(EmailAction).filter(
                EmailAction.email_id == str(email.id)
            ).all()
            
            if actions:
                print(f"   📎 Actions: {len(actions)} action(s) created")
                for action in actions:
                    print(f"      - {action.action_type} ({action.status})")
    
    def inspect_events(self, limit: int = 10):
        """Inspect event records"""
        print("\n" + "=" * 80)
        print("📨 EVENT RECORDS (Celery Queue)")
        print("=" * 80)
        
        # Get total counts by workflow type
        workflow_counts = self.db.query(
            Event.workflow_type,
            func.count(Event.id)
        ).group_by(Event.workflow_type).all()
        
        print(f"\n📊 Statistics:")
        for workflow_type, count in workflow_counts:
            print(f"   {workflow_type}: {count} events")
        
        # Get recent events
        events = self.db.query(Event).order_by(
            desc(Event.created_at)
        ).limit(limit).all()
        
        print(f"\n📋 Recent Events (showing {len(events)}):")
        print("-" * 80)
        
        for event in events:
            print(f"\n📨 Event ID: {event.id}")
            print(f"   Workflow: {event.workflow_type}")
            print(f"   Created: {event.created_at}")
            print(f"   Updated: {event.updated_at}")
            
            # Show event data
            if event.data:
                print(f"   Data Keys: {list(event.data.keys())}")
                if 'email_id' in event.data:
                    print(f"   Email ID: {event.data['email_id']}")
                if 'subject' in event.data:
                    print(f"   Subject: {event.data['subject']}")
            
            # Show task context (results)
            if event.task_context:
                print(f"   ✅ Processed: Yes")
                print(f"   Task Context: {event.task_context}")
            else:
                print(f"   ⏳ Processed: No (pending)")
    
    def inspect_email_actions(self, limit: int = 20):
        """Inspect email action records"""
        print("\n" + "=" * 80)
        print("🎯 EMAIL ACTION RECORDS")
        print("=" * 80)
        
        # Get counts by status
        status_counts = self.db.query(
            EmailAction.status,
            func.count(EmailAction.id)
        ).group_by(EmailAction.status).all()
        
        # Get counts by type
        type_counts = self.db.query(
            EmailAction.action_type,
            func.count(EmailAction.id)
        ).group_by(EmailAction.action_type).all()
        
        print(f"\n📊 Statistics:")
        print("   By Status:")
        for status, count in status_counts:
            print(f"      {status}: {count}")
        
        print("   By Type:")
        for action_type, count in type_counts:
            print(f"      {action_type}: {count}")
        
        # Get recent actions
        actions = self.db.query(EmailAction).order_by(
            desc(EmailAction.created_at)
        ).limit(limit).all()
        
        print(f"\n📋 Recent Actions (showing {len(actions)}):")
        print("-" * 80)
        
        for action in actions:
            print(f"\n🎯 Action ID: {action.id}")
            print(f"   Email ID: {action.email_id}")
            print(f"   Type: {action.action_type}")
            print(f"   Status: {action.status}")
            print(f"   Confidence: {action.confidence_score}")
            print(f"   Created: {action.created_at}")
            print(f"   Reasoning: {action.reasoning[:100]}...")
            
            # Check staging data
            if action.action_type == 'log_call':
                staging = self.db.query(CallLogStaging).filter(
                    CallLogStaging.email_action_id == action.id
                ).first()
                if staging:
                    print(f"   📞 Call Log: {staging.subject}")
            elif action.action_type == 'add_note':
                staging = self.db.query(NoteStaging).filter(
                    NoteStaging.email_action_id == action.id
                ).first()
                if staging:
                    print(f"   📝 Note: {staging.note_content[:50]}...")
            elif action.action_type == 'set_reminder':
                staging = self.db.query(ReminderStaging).filter(
                    ReminderStaging.email_action_id == action.id
                ).first()
                if staging:
                    print(f"   ⏰ Reminder: {staging.reminder_text[:50]}...")
    
    def find_email_by_subject(self, subject_keyword: str):
        """Find emails by subject keyword"""
        print(f"\n🔍 Searching for emails with subject containing: '{subject_keyword}'")
        print("-" * 80)
        
        emails = self.db.query(Email).filter(
            Email.subject.ilike(f'%{subject_keyword}%')
        ).order_by(desc(Email.date)).limit(10).all()
        
        if not emails:
            print("   No emails found")
            return
        
        print(f"   Found {len(emails)} email(s):")
        for email in emails:
            email_date = datetime.fromtimestamp(email.date) if email.date else None
            print(f"\n   📧 ID: {email.id}")
            print(f"      Subject: {email.subject}")
            print(f"      From: {email.from_email}")
            print(f"      Date: {email_date}")
            print(f"      Processed: {email.processed}")
    
    def show_summary(self):
        """Show database summary"""
        print("\n" + "=" * 80)
        print("📊 DATABASE SUMMARY")
        print("=" * 80)
        
        # Email stats
        email_total = self.db.query(Email).count()
        email_processed = self.db.query(Email).filter(Email.processed == True).count()
        email_forwarded = self.db.query(Email).filter(Email.is_forwarded == True).count()
        
        # Event stats
        event_total = self.db.query(Event).count()
        event_processed = self.db.query(Event).filter(Event.task_context != None).count()
        
        # Action stats
        action_total = self.db.query(EmailAction).count()
        action_pending = self.db.query(EmailAction).filter(EmailAction.status == 'pending').count()
        action_approved = self.db.query(EmailAction).filter(EmailAction.status == 'approved').count()
        
        print(f"\n📧 Emails:")
        print(f"   Total: {email_total}")
        print(f"   Processed: {email_processed} ({email_processed/email_total*100:.1f}%)" if email_total > 0 else "   Processed: 0")
        print(f"   Forwarded: {email_forwarded}")
        
        print(f"\n📨 Events (Celery):")
        print(f"   Total: {event_total}")
        print(f"   Processed: {event_processed} ({event_processed/event_total*100:.1f}%)" if event_total > 0 else "   Processed: 0")
        
        print(f"\n🎯 Email Actions:")
        print(f"   Total: {action_total}")
        print(f"   Pending: {action_pending}")
        print(f"   Approved: {action_approved}")
        
        # Recent activity
        print(f"\n⏱️  Recent Activity:")
        
        # Last email
        last_email = self.db.query(Email).order_by(desc(Email.created_at)).first()
        if last_email:
            print(f"   Last email synced: {last_email.created_at}")
        
        # Last action
        last_action = self.db.query(EmailAction).order_by(desc(EmailAction.created_at)).first()
        if last_action:
            print(f"   Last action created: {last_action.created_at}")
        
        # Last event
        last_event = self.db.query(Event).order_by(desc(Event.created_at)).first()
        if last_event:
            print(f"   Last event created: {last_event.created_at}")


def main():
    """Main function with CLI arguments"""
    parser = argparse.ArgumentParser(description='Inspect database state for debugging')
    parser.add_argument('command', choices=['summary', 'emails', 'events', 'actions', 'all'],
                        help='What to inspect')
    parser.add_argument('--limit', type=int, default=10,
                        help='Number of records to show (default: 10)')
    parser.add_argument('--search', type=str,
                        help='Search emails by subject keyword')
    parser.add_argument('--show-all', action='store_true',
                        help='Show all records (no limit)')
    
    args = parser.parse_args()
    
    inspector = DatabaseInspector()
    
    if args.search:
        inspector.find_email_by_subject(args.search)
    elif args.command == 'summary':
        inspector.show_summary()
    elif args.command == 'emails':
        inspector.inspect_emails(limit=args.limit, show_all=args.show_all)
    elif args.command == 'events':
        inspector.inspect_events(limit=args.limit)
    elif args.command == 'actions':
        inspector.inspect_email_actions(limit=args.limit)
    elif args.command == 'all':
        inspector.show_summary()
        inspector.inspect_emails(limit=args.limit)
        inspector.inspect_events(limit=args.limit)
        inspector.inspect_email_actions(limit=args.limit)


if __name__ == "__main__":
    main()