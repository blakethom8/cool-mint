#!/usr/bin/env python3
"""Test specific emails that should trigger note creation"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from database.session import db_session
from database.data_models.email_data import Email
from database.data_models.email_actions import EmailAction, NoteStaging
from workflows.email_actions.email_actions_workflow import EmailActionsWorkflow
from schemas.email_actions_schema import EmailActionsEventSchema


def test_email_note(email_id: str):
    """Test note creation for a specific email"""
    
    print(f"\n{'='*60}")
    print(f"Testing Email ID: {email_id}")
    print('='*60)
    
    # Get email from database
    for session in db_session():
        email = session.query(Email).filter_by(id=email_id).first()
        
        if not email:
            print(f"Email {email_id} not found!")
            return
        
        # Create event
        event = EmailActionsEventSchema(
            email_id=str(email.id),
            content=email.conversation_for_llm or email.body_plain or email.body,
            subject=email.subject,
            from_email=email.from_email,
            is_forwarded=email.is_forwarded or False,
            user_instruction=email.user_instruction
        )
        break
    
    print(f"Subject: {event.subject}")
    print(f"From: {event.from_email}")
    print(f"Forwarded: {event.is_forwarded}")
    if event.user_instruction:
        print(f"User Instruction: {event.user_instruction}")
    
    # Run workflow
    workflow = EmailActionsWorkflow()
    result = workflow.run(event.model_dump())
    
    # Check results
    classification = result.nodes.get("IntentClassificationNode", {})
    print(f"\nClassified as: {classification.get('action_type')} (confidence: {classification.get('confidence_score')})")
    
    if classification.get('action_type') == 'add_note':
        # Check extraction
        extraction = result.nodes.get("AddNoteExtractionNode", {})
        note_params = extraction.get("note_parameters", {})
        
        print(f"\nExtracted Note Data:")
        print(f"  Type: {note_params.get('note_type')}")
        print(f"  Sentiment: {note_params.get('sentiment')}")
        print(f"  Topics: {note_params.get('topics')}")
        print(f"  Entities: {len(note_params.get('mentioned_entities', []))}")
        
        # Check entity matching
        matching = result.nodes.get("EntityMatchingNode", {})
        print(f"\nEntity Matching: {matching.get('match_status')}")
        
        # Check staging
        staging = result.nodes.get("CreateStagingRecordNode", {})
        if staging.get("status") == "created":
            print(f"\n✅ Staging record created successfully!")
            
            # Query for created records
            for session in db_session():
                note_stagings = session.query(NoteStaging).join(EmailAction).filter(
                    EmailAction.email_id == email_id
                ).all()
                
                print(f"Found {len(note_stagings)} staging records")
                for staging in note_stagings:
                    print(f"\n  - Entity: {staging.related_entity_name}")
                    print(f"    Topics: {staging.llm_topics}")
                    print(f"    Sentiment: {staging.llm_sentiment}")
                break
        else:
            print(f"\n❌ Failed to create staging: {staging.get('error')}")
    else:
        print("\n⚠️  Email was not classified as add_note")


def main():
    """Test both specific emails"""
    email_ids = [
        "bd700ba3-848c-4e5f-aa17-2fee707784cf",
        "723e1c0c-c8fc-4db4-983f-75a1194ab9f2"
    ]
    
    for email_id in email_ids:
        try:
            test_email_note(email_id)
        except Exception as e:
            print(f"\n❌ Error testing {email_id}: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()