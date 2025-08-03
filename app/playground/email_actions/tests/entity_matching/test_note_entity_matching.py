#!/usr/bin/env python3
"""Test note creation workflow with entity matching"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from database.session import db_session
from database.data_models.email_data import Email
from database.data_models.email_actions import EmailAction, NoteStaging
from workflows.email_actions.email_actions_workflow import EmailActionsWorkflow
from schemas.email_actions_schema import EmailActionsEventSchema


def create_test_email():
    """Create a test email that should trigger note creation with multiple entities"""
    from uuid import uuid4
    return {
        "email_id": str(uuid4()),
        "subject": "Fwd: Important information about referral patterns",
        "from_email": "blake.thomson@example.com",
        "content": """Please add this as a note.

Important insights from the conference:

Dr. DeStefano mentioned that their orthopedic department has been seeing increased referrals from Dr. McDonald's practice at UCLA. 

Dr. Smith from Cedars has also been collaborating more closely with the cardiology team.

The new referral tracking system is showing positive results across all specialties.

Key takeaways:
- Referral patterns are improving
- Cross-specialty collaboration is increasing
- Need to follow up with all three doctors next quarter
""",
        "is_forwarded": True,
        "user_instruction": "Please add this as a note"
    }


def test_note_workflow(use_real_email=False):
    """Test the note creation workflow with entity matching"""
    
    print("=" * 60)
    print("Testing Note Creation with Entity Matching")
    print("=" * 60)
    
    if use_real_email:
        # Use a real email from the database
        for session in db_session():
            email = session.query(Email).filter(
                Email.is_forwarded == True
            ).first()
            
            if not email:
                print("No forwarded emails found in database")
                return
            
            event = EmailActionsEventSchema(
                email_id=str(email.id),
                content=email.conversation_for_llm or email.body_plain or email.body,
                subject=email.subject,
                from_email=email.from_email,
                is_forwarded=True,
                user_instruction=email.user_instruction or "Please add this as a note"
            )
            break
    else:
        # Create test event
        test_email_data = create_test_email()
        event = EmailActionsEventSchema(**test_email_data)
    
    print(f"\nTest Email:")
    print(f"From: {event.from_email}")
    print(f"Subject: {event.subject}")
    print(f"\nContent Preview:")
    print(event.content[:200] + "...\n")
    
    # Initialize workflow
    workflow = EmailActionsWorkflow()
    
    print("Running workflow...")
    result = workflow.run(event.model_dump())
    
    # Display results
    print("\n" + "=" * 60)
    print("WORKFLOW RESULTS")
    print("=" * 60)
    
    # Check classification
    classification = result.nodes.get("IntentClassificationNode", {})
    print(f"\nAction Type: {classification.get('action_type')}")
    print(f"Confidence: {classification.get('confidence_score')}")
    
    # Check extraction
    extraction = result.nodes.get("AddNoteExtractionNode", {})
    note_params = extraction.get("note_parameters", {})
    
    print(f"\nExtracted Note:")
    print(f"Type: {note_params.get('note_type')}")
    print(f"Sentiment: {note_params.get('sentiment')}")
    print(f"Topics: {note_params.get('topics')}")
    print(f"\nMentioned Entities: {len(note_params.get('mentioned_entities', []))}")
    for entity in note_params.get('mentioned_entities', []):
        print(f"  - {entity.get('name')} ({entity.get('type')})")
    
    # Check entity matching
    matching = result.nodes.get("EntityMatchingNode", {})
    matching_results = matching.get("matching_results", {})
    
    print(f"\nEntity Matching Results:")
    print(f"Status: {matching.get('match_status')}")
    print(f"Matched: {matching_results.get('matched_count', 0)}")
    print(f"Unmatched: {matching_results.get('unmatched_count', 0)}")
    
    for entity_result in matching_results.get("entities", []):
        if entity_result.get("matched"):
            print(f"\n✓ {entity_result.get('name')}")
            print(f"  → {entity_result.get('match_display_name')}")
            print(f"  ID: {entity_result.get('match_id')}")
            print(f"  Confidence: {entity_result.get('confidence'):.2f}")
            print(f"  Type: {entity_result.get('match_details', {}).get('match_type')}")
        else:
            print(f"\n✗ {entity_result.get('name')}")
            print(f"  Reason: {entity_result.get('reason')}")
    
    # Check staging records
    staging_node = result.nodes.get("CreateStagingRecordNode", {})
    if staging_node.get("status") == "created":
        print(f"\n✅ Staging records created successfully")
        print(f"Email Action ID: {staging_node.get('email_action_id')}")
        
        # Query database for created records
        for session in db_session():
            # Get the email action
            email_action = session.query(EmailAction).filter_by(
                id=staging_node.get('email_action_id')
            ).first()
            
            if email_action:
                # Get note staging records
                note_stagings = session.query(NoteStaging).filter_by(
                    email_action_id=email_action.id
                ).all()
                
                print(f"\nCreated {len(note_stagings)} note staging record(s):")
                
                for i, staging in enumerate(note_stagings, 1):
                    print(f"\n  Record #{i}:")
                    print(f"  Entity: {staging.related_entity_name} (ID: {staging.related_entity_id})")
                    print(f"  Topics: {staging.llm_topics}")
                    print(f"  Sentiment: {staging.llm_sentiment}")
                    print(f"  Match Status: {staging.entity_match_status}")
                    
                    if staging.unmatched_entities:
                        print(f"  Unmatched: {len(staging.unmatched_entities)} entities")
            break
    else:
        print(f"\n❌ Failed to create staging records: {staging_node.get('error')}")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Test note creation with entity matching")
    parser.add_argument("--migrate", action="store_true", help="Run database migration first")
    parser.add_argument("--real-email", action="store_true", help="Use a real email from database")
    args = parser.parse_args()
    
    if args.migrate:
        print("Running database migration...")
        import subprocess
        result = subprocess.run(["./migrate.sh"], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Migration completed successfully")
        else:
            print(f"❌ Migration failed: {result.stderr}")
            return
    
    try:
        test_note_workflow(use_real_email=args.real_email)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()