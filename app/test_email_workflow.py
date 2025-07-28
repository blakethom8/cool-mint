#!/usr/bin/env python3
"""
Test script for Email APIs and Workflow
Tests the complete flow from email sync to workflow processing
"""
import os
import sys
import time
from datetime import datetime, timedelta

# Add app directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.session import db_session
from services.email_service import EmailService
from services.email_sync_manager import EmailSyncManager
from database.data_models.email_data import Email
from database.data_models.email_actions import EmailAction


def test_email_sync():
    """Test manual email sync"""
    print("\n=== Testing Email Sync ===")
    try:
        sync_manager = EmailSyncManager()
        
        # Sync emails from last hour
        print("Syncing emails from the last hour...")
        results = sync_manager.sync_recent_emails(
            minutes_back=60,
            limit=10,
            process_emails=False
        )
        
        print(f"✓ Sync completed successfully!")
        print(f"  - Total fetched: {results['total_fetched']}")
        print(f"  - New emails: {results['new_emails']}")
        print(f"  - Updated emails: {results['updated_emails']}")
        print(f"  - Sync mode: {results['sync_mode']}")
        
        return True
    except Exception as e:
        print(f"✗ Sync failed: {str(e)}")
        return False


def test_list_emails():
    """Test listing emails from database"""
    print("\n=== Testing Email List ===")
    try:
        with next(db_session()) as db:
            service = EmailService(db)
            
            # List recent emails
            emails, total_count = service.list_emails(
                page=1,
                page_size=5,
                sort_by='date',
                sort_order='desc'
            )
            
            print(f"✓ Found {total_count} total emails")
            print(f"  Showing first {len(emails)} emails:")
            
            for i, email in enumerate(emails, 1):
                print(f"\n  {i}. Email ID: {email['id']}")
                print(f"     From: {email['from_email']} ({email['from_name']})")
                print(f"     Subject: {email['subject']}")
                print(f"     Date: {email['date']}")
                print(f"     Processed: {email['processed']}")
                print(f"     Status: {email['processing_status']}")
                
            return emails
    except Exception as e:
        print(f"✗ List failed: {str(e)}")
        return []


def test_process_email(email_id: str):
    """Test processing an email through the workflow"""
    print(f"\n=== Testing Email Processing for ID: {email_id} ===")
    
    try:
        from database.event import Event
        from database.repository import GenericRepository
        from workflows.workflow_registry import WorkflowRegistry
        
        with next(db_session()) as db:
            service = EmailService(db)
            
            # Get email details
            email = service.get_email_detail(email_id)
            if not email:
                print(f"✗ Email not found with ID: {email_id}")
                return False
            
            print(f"✓ Found email: {email['subject']}")
            
            # Check if already processed
            if email['processed'] and email['processing_status'] == 'completed':
                print("  Note: Email already processed")
                return True
            
            # Mark as processing
            service.mark_email_processed(email_id, status='in_progress')
            print("✓ Marked email as in_progress")
            
            # Create event for workflow
            event_data = {
                "email_id": str(email_id),
                "content": email['body'] or email['body_plain'] or '',
                "subject": email['subject'],
                "from_email": email['from_email'] or 'unknown',
                "is_forwarded": email['is_forwarded'],
                "user_instruction": email['user_instruction']
            }
            
            repository = GenericRepository(session=db, model=Event)
            event = Event(
                data=event_data,
                workflow_type=WorkflowRegistry.EMAIL_ACTIONS.name
            )
            repository.create(obj=event)
            print(f"✓ Created workflow event: {event.id}")
            
            # In a real scenario, Celery would process this
            # For testing, we'll run the workflow directly
            print("\n  Running EMAIL_ACTIONS workflow...")
            
            from core.workflow import WorkflowEngine
            workflow = WorkflowRegistry.EMAIL_ACTIONS.value()
            engine = WorkflowEngine()
            
            try:
                result = engine.run(workflow, event_data)
                print("✓ Workflow completed successfully!")
                
                # Mark as completed
                service.mark_email_processed(email_id, status='completed')
                
                return True
            except Exception as wf_error:
                print(f"✗ Workflow error: {str(wf_error)}")
                service.mark_email_processed(email_id, status='error')
                return False
                
    except Exception as e:
        print(f"✗ Processing failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_check_email_actions(email_id: str):
    """Check if email actions were created"""
    print(f"\n=== Checking Email Actions for ID: {email_id} ===")
    
    try:
        with next(db_session()) as db:
            # Query for email actions
            actions = db.query(EmailAction).filter(
                EmailAction.email_id == email_id
            ).all()
            
            if actions:
                print(f"✓ Found {len(actions)} actions for this email:")
                for action in actions:
                    print(f"\n  - Action Type: {action.action_type}")
                    print(f"    Status: {action.status}")
                    print(f"    Confidence: {action.confidence_score}")
                    print(f"    Reasoning: {action.reasoning[:100]}...")
                    print(f"    Created: {action.created_at}")
            else:
                print("✗ No actions found for this email")
                
            return actions
    except Exception as e:
        print(f"✗ Check failed: {str(e)}")
        return []


def main():
    """Run all tests"""
    print("=" * 60)
    print("Email Workflow Test Suite")
    print("=" * 60)
    
    # Test 1: Sync emails
    sync_success = test_email_sync()
    
    if not sync_success:
        print("\n❌ Email sync failed. Please check your Nylas configuration.")
        return
    
    # Test 2: List emails
    emails = test_list_emails()
    
    if not emails:
        print("\n❌ No emails found. Please check if sync worked correctly.")
        return
    
    # Test 3: Find an unprocessed email
    unprocessed_email = None
    for email in emails:
        if not email['processed']:
            unprocessed_email = email
            break
    
    if not unprocessed_email:
        print("\n⚠️  No unprocessed emails found. Using the most recent email for testing.")
        unprocessed_email = emails[0]
    
    # Test 4: Process the email
    email_id = unprocessed_email['id']
    print(f"\n📧 Selected email for processing: {unprocessed_email['subject']}")
    
    process_success = test_process_email(email_id)
    
    if process_success:
        # Wait a moment for database updates
        time.sleep(2)
        
        # Test 5: Check for created actions
        actions = test_check_email_actions(email_id)
        
        if actions:
            print("\n✅ Complete workflow test successful!")
            print(f"   Email was processed and {len(actions)} actions were created.")
        else:
            print("\n⚠️  Email processed but no actions were created.")
            print("   This might be because the email didn't contain actionable content.")
    else:
        print("\n❌ Email processing failed.")
    
    print("\n" + "=" * 60)
    print("Test Summary:")
    print(f"  - Email Sync: {'✓' if sync_success else '✗'}")
    print(f"  - Email List: {'✓' if emails else '✗'}")
    print(f"  - Email Processing: {'✓' if process_success else '✗'}")
    print("=" * 60)


if __name__ == "__main__":
    main()