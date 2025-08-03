#!/usr/bin/env python3
"""Debug script to check email actions in database"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from database.session import db_session
from database.data_models.email_actions import EmailAction, NoteStaging
from database.data_models.email_data import Email


def debug_email_actions(email_id: str):
    """Check all email actions for a specific email"""
    
    print(f"\n{'='*60}")
    print(f"Debugging Email ID: {email_id}")
    print('='*60)
    
    for session in db_session():
        # Get email
        email = session.query(Email).filter_by(id=email_id).first()
        if email:
            print(f"\nEmail found:")
            print(f"  Subject: {email.subject}")
            print(f"  From: {email.from_email}")
            print(f"  Date: {email.date}")
        
        # Get all email actions for this email
        email_actions = session.query(EmailAction).filter_by(email_id=email_id).all()
        
        print(f"\nFound {len(email_actions)} EmailAction records:")
        
        for i, action in enumerate(email_actions, 1):
            print(f"\n  Action #{i}:")
            print(f"    ID: {action.id}")
            print(f"    Type: {action.action_type}")
            print(f"    Status: {action.status}")
            print(f"    Created: {action.created_at}")
            print(f"    Confidence: {action.confidence_score}")
            
            # Get staging records for this action
            if action.action_type == 'add_note':
                stagings = session.query(NoteStaging).filter_by(email_action_id=action.id).all()
                print(f"    Note Staging Records: {len(stagings)}")
                
                for j, staging in enumerate(stagings, 1):
                    print(f"      Staging #{j}:")
                    print(f"        ID: {staging.id}")
                    print(f"        Entity: {staging.related_entity_name} (ID: {staging.related_entity_id})")
                    print(f"        Match Status: {staging.entity_match_status}")
                    print(f"        Created: {staging.created_at}")
        
        break


def main():
    """Debug both specific emails"""
    email_ids = [
        "bd700ba3-848c-4e5f-aa17-2fee707784cf",
        "723e1c0c-c8fc-4db4-983f-75a1194ab9f2"
    ]
    
    for email_id in email_ids:
        debug_email_actions(email_id)
    
    # Also check for any duplicate processing
    print(f"\n{'='*60}")
    print("Checking for duplicate processing patterns")
    print('='*60)
    
    for session in db_session():
        # Count email actions by email_id
        from sqlalchemy import func
        
        duplicates = session.query(
            EmailAction.email_id,
            EmailAction.action_type,
            func.count(EmailAction.id).label('count')
        ).group_by(
            EmailAction.email_id,
            EmailAction.action_type
        ).having(
            func.count(EmailAction.id) > 1
        ).all()
        
        if duplicates:
            print(f"\nFound {len(duplicates)} emails with multiple actions of same type:")
            for dup in duplicates[:10]:  # Show first 10
                print(f"  Email: {dup.email_id}, Type: {dup.action_type}, Count: {dup.count}")
        else:
            print("\nNo duplicate action types found for any email")
        
        break


if __name__ == "__main__":
    main()