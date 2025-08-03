#!/usr/bin/env python3
"""Test reminder workflow with entity matching"""

import sys
from pathlib import Path
from datetime import datetime

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from database.session import db_session
from database.data_models.email_data import Email
from database.data_models.email_actions import EmailAction, ReminderStaging
from workflows.email_actions.email_actions_workflow import EmailActionsWorkflow
from schemas.email_actions_schema import EmailActionsEventSchema


def test_reminder_workflow(email_content: str, subject: str = "Reminder Test", user_instruction: str = None):
    """Test the reminder workflow with entity matching"""
    
    print("=" * 60)
    print("Testing Reminder Workflow with Entity Matching")
    print("=" * 60)
    
    # Create test event
    from uuid import uuid4
    event = EmailActionsEventSchema(
        email_id=str(uuid4()),
        content=email_content,
        subject=subject,
        from_email="test@example.com",
        is_forwarded=False,
        user_instruction=user_instruction
    )
    
    print(f"\nTest Email:")
    print(f"Subject: {event.subject}")
    print(f"From: {event.from_email}")
    print(f"Content: {event.content[:100]}...")
    if event.user_instruction:
        print(f"User Instruction: {event.user_instruction}")
    
    # Run workflow
    workflow = EmailActionsWorkflow()
    result = workflow.run(event.model_dump())
    
    # Display results
    print("\n" + "=" * 60)
    print("WORKFLOW RESULTS")
    print("=" * 60)
    
    # Check classification
    classification = result.nodes.get("IntentClassificationNode", {})
    print(f"\nAction Type: {classification.get('action_type')}")
    print(f"Confidence: {classification.get('confidence_score')}")
    
    if classification.get('action_type') == 'set_reminder':
        # Check extraction
        extraction = result.nodes.get("SetReminderExtractionNode", {})
        reminder_params = extraction.get("reminder_parameters", {})
        
        print(f"\nExtracted Reminder:")
        print(f"  Text: {reminder_params.get('reminder_text')}")
        print(f"  Due Date: {reminder_params.get('due_date')}")
        print(f"  Priority: {reminder_params.get('priority')}")
        print(f"  Assignee: {reminder_params.get('assignee')}")
        print(f"  Related Entity: {reminder_params.get('related_entity_name')}")
        print(f"  Type: {reminder_params.get('reminder_type')}")
        print(f"  Entities: {len(reminder_params.get('mentioned_entities', []))}")
        
        for entity in reminder_params.get('mentioned_entities', []):
            print(f"    - {entity.get('name')} ({entity.get('type')})")
        
        # Check entity matching
        matching = result.nodes.get("EntityMatchingNode", {})
        matching_results = matching.get("matching_results", {})
        
        print(f"\nEntity Matching Results:")
        print(f"  Status: {matching.get('match_status')}")
        print(f"  Matched: {matching_results.get('matched_count', 0)}")
        print(f"  Unmatched: {matching_results.get('unmatched_count', 0)}")
        
        for entity_result in matching_results.get("entities", []):
            if entity_result.get("matched"):
                print(f"\n  ✓ {entity_result.get('name')}")
                print(f"    → {entity_result.get('match_display_name')}")
                print(f"    ID: {entity_result.get('match_id')}")
                print(f"    Confidence: {entity_result.get('confidence'):.2f}")
            else:
                print(f"\n  ✗ {entity_result.get('name')}")
                print(f"    Reason: {entity_result.get('reason')}")
        
        # Check staging
        staging_node = result.nodes.get("CreateStagingRecordNode", {})
        if staging_node.get("status") == "created":
            print(f"\n✅ Staging record created successfully")
            print(f"Email Action ID: {staging_node.get('email_action_id')}")
            
            # Query database for created record
            for session in db_session():
                email_action = session.query(EmailAction).filter_by(
                    id=staging_node.get('email_action_id')
                ).first()
                
                if email_action:
                    reminder_staging = session.query(ReminderStaging).filter_by(
                        email_action_id=email_action.id
                    ).first()
                    
                    if reminder_staging:
                        print(f"\nCreated Reminder Staging:")
                        print(f"  Reminder: {reminder_staging.reminder_text}")
                        print(f"  Due Date: {reminder_staging.due_date}")
                        print(f"  Priority: {reminder_staging.priority}")
                        print(f"  Assignee: {reminder_staging.assignee}")
                        if reminder_staging.assignee_id:
                            print(f"  Assignee ID: {reminder_staging.assignee_id}")
                        print(f"  Related Entity: {reminder_staging.related_entity_name}")
                        if reminder_staging.related_entity_id:
                            print(f"  Related Entity ID: {reminder_staging.related_entity_id}")
                        print(f"  Category: {reminder_staging.llm_reminder_category}")
                        print(f"  Match Status: {reminder_staging.entity_match_status}")
                        
                        if reminder_staging.unmatched_entities:
                            print(f"  Unmatched: {len(reminder_staging.unmatched_entities)} entities")
                break
        else:
            print(f"\n❌ Failed to create staging: {staging_node.get('error')}")
    else:
        print("\n⚠️  Email was not classified as set_reminder")
    
    return result


def main():
    """Run test cases"""
    
    # Test 1: Reminder with specific person
    print("\n\nTEST 1: Reminder with Specific Person")
    print("-" * 60)
    
    test_reminder_workflow(
        email_content="""Remind me to follow up with Dr. DeStefano in 60 days about the referral program results.
        
        We need to check on:
        - Number of referrals received
        - Success rate of the program
        - Any feedback from participating physicians
        """,
        subject="Follow-up reminder needed",
        user_instruction="Set a reminder"
    )
    
    # Test 2: Reminder with multiple entities
    print("\n\nTEST 2: Reminder with Multiple Entities")
    print("-" * 60)
    
    test_reminder_workflow(
        email_content="""Please set a reminder for next Friday to call Dr. Smith and Dr. Johnson from Cedar Sinai about the collaboration meeting.
        
        Make sure to discuss the new protocol implementation timeline.
        """,
        subject="Reminder: Call doctors next week",
        user_instruction="Set reminder"
    )
    
    # Test 3: Task assignment reminder
    print("\n\nTEST 3: Task Assignment Reminder")
    print("-" * 60)
    
    test_reminder_workflow(
        email_content="""Assign Blake Thomson to prepare the quarterly report for UCLA Medical Center by end of month.
        
        The report should include:
        - Activity summary
        - Key achievements
        - Next quarter goals
        """,
        subject="Task: Quarterly report preparation"
    )
    
    # Run database migration if needed
    print("\n\nNote: If you get database errors, run: ./migrate.sh")


if __name__ == "__main__":
    main()