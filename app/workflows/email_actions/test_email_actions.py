#!/usr/bin/env python3
"""
Test script for EmailActionsWorkflow
"""
import argparse
from datetime import datetime
from uuid import UUID
import sys
import os
import json

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
os.chdir(project_root)

from database.session import db_session
from database.data_models.email_data import Email
from database.data_models.email_parsed_data import EmailParsed  # Import to ensure relationship is loaded
from database.data_models.email_actions import EmailAction, CallLogStaging, NoteStaging, ReminderStaging
from workflows.email_actions.email_actions_workflow import EmailActionsWorkflow
from schemas.email_actions_schema import EmailActionsEventSchema


def test_email_actions_workflow(email_id: str = None):
    """Test the email actions workflow with a specific email"""
    
    for session in db_session():
        # Get email to process
        if email_id:
            try:
                email_uuid = UUID(email_id)
                email = session.query(Email).filter(Email.id == email_uuid).first()
            except ValueError:
                # Try by nylas_id
                email = session.query(Email).filter(Email.nylas_id == email_id).first()
        else:
            # Get most recent email
            email = session.query(Email).order_by(Email.received_at.desc()).first()
        
        if not email:
            print("No email found to process")
            return
        
        print(f"\n📧 Processing Email:")
        print(f"  ID: {email.id}")
        print(f"  Subject: {email.subject}")
        print(f"  From: {email.from_email}")
        print(f"  Date: {email.received_at}")
        
        if email.is_forwarded:
            print(f"\n  This is a forwarded email")
            if email.user_instruction:
                print(f"  User instruction: {email.user_instruction[:100]}...")
        
        # Create event for workflow
        event = EmailActionsEventSchema(
            email_id=str(email.id),
            content=email.conversation_for_llm or email.body_plain or email.body_html,
            subject=email.subject,
            from_email=email.from_email,
            is_forwarded=email.is_forwarded,
            user_instruction=email.user_instruction
        )
        
        # Initialize workflow
        workflow = EmailActionsWorkflow()
        
        print("\n🔄 Running EmailActionsWorkflow...")
        
        # Run workflow
        result = workflow.run(event.model_dump())
        
        # Check results
        session.refresh(email)
        
        # Get email actions created
        actions = session.query(EmailAction).filter(
            EmailAction.email_id == email.id
        ).order_by(EmailAction.created_at.desc()).all()
        
        if actions:
            print(f"\n✅ Created {len(actions)} email action(s):")
            
            for action in actions:
                print(f"\n  Action Type: {action.action_type}")
                print(f"  Confidence: {action.confidence_score:.2f}")
                print(f"  Reasoning: {action.reasoning}")
                print(f"  Status: {action.status}")
                
                # Check for staging records
                if action.action_type == 'log_call':
                    staging = session.query(CallLogStaging).filter(
                        CallLogStaging.email_action_id == action.id
                    ).first()
                    if staging:
                        print(f"\n  📞 Call Log Staging:")
                        print(f"     Subject: {staging.subject}")
                        print(f"     Date: {staging.activity_date}")
                        print(f"     Duration: {staging.duration_minutes} minutes")
                        print(f"     Type: {staging.mno_type}")
                        print(f"     Setting: {staging.mno_setting}")
                        if staging.contact_ids:
                            print(f"     Participants: {', '.join(staging.contact_ids)}")
                        
                elif action.action_type == 'add_note':
                    staging = session.query(NoteStaging).filter(
                        NoteStaging.email_action_id == action.id
                    ).first()
                    if staging:
                        print(f"\n  📝 Note Staging:")
                        print(f"     Title: {staging.note_title}")
                        print(f"     Content: {staging.note_content[:100]}...")
                        print(f"     Related Contact: {staging.related_contact}")
                        
                elif action.action_type == 'set_reminder':
                    staging = session.query(ReminderStaging).filter(
                        ReminderStaging.email_action_id == action.id
                    ).first()
                    if staging:
                        print(f"\n  ⏰ Reminder Staging:")
                        print(f"     Title: {staging.reminder_title}")
                        print(f"     Due Date: {staging.due_date}")
                        print(f"     Priority: {staging.priority}")
                        print(f"     Related Contact: {staging.related_contact}")
        else:
            print("\n❌ No email actions were created")
        
        print("\n✅ Workflow execution completed")
        break


def list_emails():
    """List available emails to process"""
    for session in db_session():
        emails = session.query(Email).order_by(Email.received_at.desc()).limit(10).all()
        
        print("\n📧 Recent Emails:")
        for email in emails:
            print(f"\n  ID: {email.id}")
            print(f"  Subject: {email.subject}")
            print(f"  From: {email.from_email}")
            print(f"  Date: {email.received_at}")
            print(f"  Forwarded: {'Yes' if email.is_forwarded else 'No'}")
            if email.user_instruction:
                print(f"  Instruction: {email.user_instruction[:50]}...")
        break


def main():
    parser = argparse.ArgumentParser(description="Test EmailActionsWorkflow")
    parser.add_argument("email_id", nargs="?", help="Email ID to process (optional)")
    parser.add_argument("--list", action="store_true", help="List available emails")
    
    args = parser.parse_args()
    
    if args.list:
        list_emails()
    else:
        test_email_actions_workflow(args.email_id)


if __name__ == "__main__":
    main()