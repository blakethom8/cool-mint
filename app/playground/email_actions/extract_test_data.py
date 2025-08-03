#!/usr/bin/env python3
"""Extract sample emails from database for testing"""
import json
from pathlib import Path
from utils.base import get_sample_emails, db_session
from database.data_models.email_actions import EmailAction, CallLogStaging


def extract_emails_with_actions():
    """Extract emails that have been processed through the workflow"""
    emails_with_actions = []
    
    for session in db_session():
        # Get emails with actions
        actions = session.query(EmailAction).filter(
            EmailAction.action_type == 'log_call'
        ).order_by(EmailAction.created_at.desc()).limit(20).all()
        
        for action in actions:
            email = action.email
            staging = session.query(CallLogStaging).filter(
                CallLogStaging.email_action_id == action.id
            ).first()
            
            email_data = {
                'email': {
                    'id': str(email.id),
                    'subject': email.subject,
                    'from_email': email.from_email,
                    'user_instruction': email.user_instruction,
                    'content': email.conversation_for_llm or email.body_plain,
                    'received_at': email.received_at.isoformat() if email.received_at else None
                },
                'classification': {
                    'action_type': action.action_type,
                    'confidence_score': action.confidence_score,
                    'reasoning': action.reasoning
                }
            }
            
            if staging:
                email_data['extraction'] = {
                    'subject': staging.subject,
                    'description': staging.description,
                    'activity_date': staging.activity_date.isoformat() if staging.activity_date else None,
                    'duration_minutes': staging.duration_minutes,
                    'mno_type': staging.mno_type,
                    'mno_subtype': staging.mno_subtype,
                    'mno_setting': staging.mno_setting,
                    'participants': staging.contact_ids or []
                }
            
            emails_with_actions.append(email_data)
    
    return emails_with_actions


def save_test_data():
    """Save test data files"""
    test_data_dir = Path(__file__).parent / 'test_data'
    test_data_dir.mkdir(exist_ok=True)
    
    # Extract emails with actions
    print("Extracting emails with actions...")
    emails_with_actions = extract_emails_with_actions()
    
    if emails_with_actions:
        with open(test_data_dir / 'emails_with_actions.json', 'w') as f:
            json.dump(emails_with_actions, f, indent=2, default=str)
        print(f"Saved {len(emails_with_actions)} emails with actions")
    
    # Extract general sample emails
    print("\nExtracting general sample emails...")
    sample_emails = get_sample_emails(limit=20)
    
    if sample_emails:
        with open(test_data_dir / 'sample_emails.json', 'w') as f:
            json.dump(sample_emails, f, indent=2, default=str)
        print(f"Saved {len(sample_emails)} sample emails")
    
    # Create specific test cases
    test_cases = [
        {
            'name': 'log_call_md_to_md',
            'user_instruction': 'log an MD-to-MD lunch meeting with Dr. McDonald',
            'expected_action': 'log_call',
            'expected_fields': {
                'mno_type': 'MD_to_MD_Visits',
                'is_md_to_md': True
            }
        },
        {
            'name': 'set_reminder_follow_up',
            'user_instruction': 'remind me to follow up with them in 60 days',
            'expected_action': 'set_reminder',
            'expected_fields': {
                'due_days': 60
            }
        },
        {
            'name': 'add_note_capture',
            'user_instruction': 'capture the notes from this thread',
            'expected_action': 'add_note'
        }
    ]
    
    with open(test_data_dir / 'test_cases.json', 'w') as f:
        json.dump(test_cases, f, indent=2)
    print(f"\nSaved {len(test_cases)} test cases")


if __name__ == '__main__':
    save_test_data()