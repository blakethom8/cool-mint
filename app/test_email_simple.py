#!/usr/bin/env python3
"""
Simple test to check emails in database and test workflow
"""
import os
import sys
from datetime import datetime

# Add app directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.session import db_session
from database.data_models.email_data import Email
from database.data_models.email_actions import EmailAction
from services.email_service import EmailService


def check_recent_emails():
    """Check for recent emails in the database"""
    print("\n=== Checking Recent Emails in Database ===")
    
    with next(db_session()) as db:
        # Query for recent emails
        recent_emails = db.query(Email).order_by(Email.date.desc()).limit(5).all()
        
        if not recent_emails:
            print("❌ No emails found in database")
            return None
            
        print(f"✓ Found {len(recent_emails)} recent emails:\n")
        
        for i, email in enumerate(recent_emails, 1):
            # Convert timestamp to readable date
            email_date = datetime.fromtimestamp(email.date) if email.date else None
            
            print(f"{i}. Email ID: {email.id}")
            print(f"   From: {email.from_email}")
            print(f"   Subject: {email.subject}")
            print(f"   Date: {email_date}")
            print(f"   Processed: {email.processed}")
            print(f"   Status: {email.processing_status}")
            print(f"   Forwarded: {email.is_forwarded}")
            print(f"   Has Body: {'Yes' if email.body else 'No'}")
            print()
            
        # Return the most recent unprocessed email, or just the most recent
        for email in recent_emails:
            if not email.processed:
                return email
        
        return recent_emails[0]


def check_existing_actions():
    """Check all email actions in the database"""
    print("\n=== Checking Existing Email Actions ===")
    
    with next(db_session()) as db:
        # Query for all email actions
        actions = db.query(EmailAction).order_by(EmailAction.created_at.desc()).limit(10).all()
        
        if not actions:
            print("❌ No email actions found in database")
            return
            
        print(f"✓ Found {len(actions)} recent email actions:\n")
        
        for action in actions:
            print(f"Action ID: {action.id}")
            print(f"  Email ID: {action.email_id}")
            print(f"  Type: {action.action_type}")
            print(f"  Status: {action.status}")
            print(f"  Confidence: {action.confidence_score}")
            print(f"  Created: {action.created_at}")
            print()


def test_api_endpoints():
    """Test the API endpoints using curl"""
    print("\n=== Testing API Endpoints ===")
    
    # Test emails list endpoint
    print("\n1. Testing GET /api/emails")
    os.system('curl -s http://localhost:8080/api/emails?page=1&page_size=5 | python -m json.tool | head -20')
    
    # Test stats endpoint
    print("\n\n2. Testing GET /api/email-actions/stats")
    os.system('curl -s http://localhost:8080/api/email-actions/stats | python -m json.tool')


def main():
    """Run simple tests"""
    print("=" * 60)
    print("Email Database Check")
    print("=" * 60)
    
    # Check for recent emails
    recent_email = check_recent_emails()
    
    # Check existing actions
    check_existing_actions()
    
    # Test API endpoints if server is running
    print("\n" + "=" * 60)
    print("API Endpoint Tests (requires server running)")
    print("=" * 60)
    
    try:
        import requests
        response = requests.get("http://localhost:8080/api/email-actions/stats", timeout=2)
        if response.status_code == 200:
            test_api_endpoints()
        else:
            print("⚠️  Server returned status:", response.status_code)
    except:
        print("⚠️  Server not running or not accessible at http://localhost:8080")
        print("   Start the server with: uvicorn main:app --host 0.0.0.0 --port 8080 --reload")
    
    if recent_email:
        print(f"\n\n💡 To process the most recent email via API:")
        print(f"   curl -X POST http://localhost:8080/api/emails/{recent_email.id}/process")


if __name__ == "__main__":
    main()