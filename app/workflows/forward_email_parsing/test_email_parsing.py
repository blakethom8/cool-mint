#!/usr/bin/env python3
"""
Test script for email parsing workflow

Usage:
    python test_email_parsing.py                    # Parse most recent forwarded email
    python test_email_parsing.py <email_id>         # Parse specific email by ID
    python test_email_parsing.py --list             # List available emails
"""

import os
import sys
import argparse
from uuid import uuid4, UUID

# Add the app directory to Python path
app_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, app_dir)

from dotenv import load_dotenv
load_dotenv()

from database.session import db_session
from database.data_models.email_data import Email
from workflows.forward_email_parsing_workflow import ForwardEmailParsingWorkflow
from schemas.email_parsing_schema import EmailParsingEventSchema


def list_emails():
    """List available emails in the database"""
    for session in db_session():
        emails = session.query(Email).order_by(Email.date.desc()).limit(20).all()
        
        print("\nAvailable Emails:")
        print("=" * 100)
        print(f"{'ID':<38} {'Subject':<40} {'From':<20}")
        print("-" * 100)
        
        for email in emails:
            subject = email.subject[:37] + "..." if len(email.subject) > 40 else email.subject
            from_email = email.from_email[:17] + "..." if len(email.from_email) > 20 else email.from_email
            print(f"{str(email.id):<38} {subject:<40} {from_email:<20}")
        
        print(f"\nTotal: {len(emails)} emails (showing most recent 20)")
        break


def parse_email_by_id(email_id: str):
    """Parse a specific email by ID"""
    try:
        # Validate UUID
        uuid_obj = UUID(email_id)
    except ValueError:
        print(f"Error: '{email_id}' is not a valid UUID")
        return
    
    for session in db_session():
        email = session.query(Email).filter(Email.id == uuid_obj).first()
        
        if not email:
            print(f"Error: No email found with ID {email_id}")
            return
        
        run_workflow_on_email(email)
        break


def test_parse_forwarded_email():
    """Test parsing a forwarded email"""
    
    # Get a forwarded email from the database
    for session in db_session():
        # Find the "Fwd: Ortho Lunch" email
        email = session.query(Email).filter(
            Email.subject.ilike('%Fwd:%')
        ).order_by(Email.date.desc()).first()
        
        if not email:
            print("No forwarded email found in database")
            return
        
        run_workflow_on_email(email)
        break


def run_workflow_on_email(email: Email):
    """Run the parsing workflow on a specific email"""
    print(f"\n{'='*80}")
    print("TESTING EMAIL PARSING WORKFLOW")
    print(f"{'='*80}")
    print(f"Email: {email.subject}")
    print(f"From: {email.from_email}")
    print(f"Date: {email.date}")
    print(f"Email ID: {email.id}")
    
    # Create event for workflow
    event_data = {
        "email_id": email.id,
        "subject": email.subject,
        "from_email": email.from_email,
        "from_name": email.from_name,
        "to_emails": email.to_emails or [],
        "body": email.body,
        "body_plain": email.body_plain,
        "snippet": email.snippet,
        "date": email.date,
        "thread_id": email.thread_id,
        "nylas_id": email.nylas_id,
        "force_reparse": True  # Force re-parsing for testing
    }
    
    # Create and run workflow
    print("\nRunning email parsing workflow...")
    workflow = ForwardEmailParsingWorkflow()
    
    try:
        result = workflow.run(event_data)
        
        print("\n" + "="*80)
        print("WORKFLOW RESULTS")
        print("="*80)
        
        # Print results from each node
        for node_name, node_data in result.nodes.items():
            print(f"\n[{node_name}]")
            
            # Print key results
            if node_name == "EmailTypeDetectionNode":
                print(f"  Email Type: {node_data.get('email_type')}")
                print(f"  Is Forwarded: {node_data.get('is_forwarded')}")
                print(f"  Confidence: {node_data.get('results', {}).get('confidence')}")
            
            elif node_name == "ForwardedEmailExtractionNode":
                print(f"  User Request: {node_data.get('user_request')}")
                print(f"  Request Intents: {node_data.get('request_intents')}")
            
            elif node_name == "EntityExtractionNode":
                people = node_data.get('people', [])
                print(f"  People Found: {len(people)}")
                for person in people[:3]:
                    print(f"    - {person.get('name')} ({person.get('role')})")
            
            elif node_name == "MeetingDetailsExtractionNode":
                meeting_info = node_data.get('meeting_info')
                if meeting_info:
                    print(f"  Meeting Type: {meeting_info.get('type')}")
                    print(f"  Topics: {meeting_info.get('topics')}")
            
            elif node_name == "ActionItemExtractionNode":
                action_items = node_data.get('action_items', [])
                print(f"  Action Items: {len(action_items)}")
                for item in action_items[:3]:
                    print(f"    - {item.get('task')}")
            
            elif node_name == "SaveParsedEmailNode":
                print(f"  Status: {node_data.get('status')}")
                print(f"  Parsed Email ID: {node_data.get('parsed_email_id')}")
        
        # Check if parsing was saved
        if result.nodes.get("SaveParsedEmailNode", {}).get("status") == "saved":
            parsed_id = result.nodes["SaveParsedEmailNode"]["parsed_email_id"]
            print(f"\n✅ Successfully parsed and saved email (ID: {parsed_id})")
        else:
            print("\n❌ Failed to save parsed email")
            
    except Exception as e:
        print(f"\n❌ Error running workflow: {e}")
        import traceback
        traceback.print_exc()


def test_parse_direct_email():
    """Test parsing a direct (non-forwarded) email"""
    
    # Get a direct email from the database
    for session in db_session():
        # Find a non-forwarded email
        email = session.query(Email).filter(
            ~Email.subject.ilike('%Fwd:%')
        ).order_by(Email.date.desc()).first()
        
        if not email:
            print("No direct email found in database")
            return
        
        print(f"\n{'='*80}")
        print("TESTING DIRECT EMAIL PARSING")
        print(f"{'='*80}")
        print(f"Email: {email.subject}")
        print(f"From: {email.from_email}")
        
        # Create event for workflow
        event_data = {
            "email_id": email.id,
            "subject": email.subject,
            "from_email": email.from_email,
            "from_name": email.from_name,
            "to_emails": email.to_emails or [],
            "body": email.body,
            "body_plain": email.body_plain,
            "snippet": email.snippet,
            "date": email.date,
            "thread_id": email.thread_id,
            "nylas_id": email.nylas_id,
            "force_reparse": True
        }
        
        # Create and run workflow
        workflow = ForwardEmailParsingWorkflow()
        
        try:
            result = workflow.run(event_data)
            
            # Check email type detection
            email_type = result.nodes.get("EmailTypeDetectionNode", {}).get("email_type")
            print(f"\nDetected as: {email_type}")
            
            if result.nodes.get("SaveParsedEmailNode", {}).get("status") == "saved":
                print("✅ Successfully parsed direct email")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        
        break


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test email parsing workflow")
    parser.add_argument("email_id", nargs="?", help="Email ID to parse (optional)")
    parser.add_argument("--list", action="store_true", help="List available emails")
    
    args = parser.parse_args()
    
    if args.list:
        list_emails()
    elif args.email_id:
        parse_email_by_id(args.email_id)
    else:
        print("Email Parsing Workflow Test")
        print("=" * 80)
        
        # Test forwarded email parsing
        test_parse_forwarded_email()
        
        # Test direct email parsing
        print("\n" * 2)
        test_parse_direct_email()