#!/usr/bin/env python3
"""Test call log workflow with entity matching"""

import sys
from pathlib import Path
from datetime import datetime

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from database.session import db_session
from database.data_models.email_actions import EmailAction, CallLogStaging
from workflows.email_actions.email_actions_workflow import EmailActionsWorkflow
from schemas.email_actions_schema import EmailActionsEventSchema


def test_call_log_workflow(email_content: str, subject: str = "Call Log Test", user_instruction: str = None):
    """Test the call log workflow with entity matching"""
    
    print("=" * 60)
    print("Testing Call Log Workflow with Entity Matching")
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
    
    if classification.get('action_type') == 'log_call':
        # Check extraction
        extraction = result.nodes.get("LogCallExtractionNode", {})
        call_params = extraction.get("call_log_parameters", {})
        
        print(f"\nExtracted Call Log:")
        print(f"  Subject: {call_params.get('subject')}")
        print(f"  Activity Type: {call_params.get('activity_type')}")
        print(f"  Setting: {call_params.get('meeting_setting')}")
        print(f"  Participants: {len(call_params.get('participants', []))}")
        
        for participant in call_params.get('participants', []):
            if isinstance(participant, dict):
                print(f"    - {participant.get('name')} ({participant.get('role', 'N/A')})")
            else:
                print(f"    - {participant}")
        
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
                    call_staging = session.query(CallLogStaging).filter_by(
                        email_action_id=email_action.id
                    ).first()
                    
                    if call_staging:
                        print(f"\nCreated Call Log Staging:")
                        print(f"  Subject: {call_staging.subject}")
                        print(f"  MNO Type: {call_staging.mno_type}")
                        print(f"  Setting: {call_staging.mno_setting}")
                        print(f"  Contact IDs: {call_staging.contact_ids}")
                        print(f"  Primary Contact ID: {call_staging.primary_contact_id}")
                        print(f"  Match Status: {call_staging.entity_match_status}")
                        
                        if call_staging.matched_participant_ids:
                            print(f"\n  Matched Participants: {len(call_staging.matched_participant_ids)}")
                            for participant in call_staging.matched_participant_ids:
                                print(f"    - {participant.get('name')} (ID: {participant.get('id')})")
                                print(f"      Confidence: {participant.get('confidence')}")
                        
                        if call_staging.unmatched_participants:
                            print(f"\n  Unmatched: {len(call_staging.unmatched_participants)} participants")
                            for participant in call_staging.unmatched_participants:
                                print(f"    - {participant.get('name')}")
                break
        else:
            print(f"\n❌ Failed to create staging: {staging_node.get('error')}")
    else:
        print("\n⚠️  Email was not classified as log_call")
    
    return result


def main():
    """Run test cases"""
    
    # Test 1: Call with single participant
    print("\n\nTEST 1: Call with Single Participant")
    print("-" * 60)
    
    test_call_log_workflow(
        email_content="""Had a great MD-to-MD lunch meeting with Dr. DeStefano today.
        
        We discussed:
        - New referral patterns
        - Collaboration opportunities
        - Patient care improvements
        
        Very productive conversation. She's interested in monthly follow-ups.
        """,
        subject="MD-to-MD Lunch with Dr. DeStefano",
        user_instruction="Log this call"
    )
    
    # Test 2: Call with multiple participants
    print("\n\nTEST 2: Call with Multiple Participants")
    print("-" * 60)
    
    test_call_log_workflow(
        email_content="""Log a virtual meeting with Dr. Smith, Dr. Johnson, and Dr. Williams from Cedar Sinai.
        
        Topics covered:
        - New treatment protocols
        - Research collaboration
        - Joint patient care initiatives
        
        Meeting lasted 45 minutes. Very engaged discussion.
        """,
        subject="Virtual meeting with Cedar Sinai team"
    )
    
    # Test 3: Mixed matched/unmatched participants
    print("\n\nTEST 3: Mixed Matched/Unmatched Participants")
    print("-" * 60)
    
    test_call_log_workflow(
        email_content="""Please log: Had a planning meeting with Dr. DeStefano, Blake Thomson, and Dr. Unknown New Person.
        
        Discussed quarterly goals and new physician outreach strategy.
        """,
        subject="Planning meeting",
        user_instruction="Log this meeting"
    )
    
    # Test without database (using testing node)
    print("\n\nTEST 4: Test Without Database Commits")
    print("-" * 60)
    
    from workflows.email_actions.email_actions_nodes import CreateStagingRecordTestingNode
    from workflows.email_actions import EmailActionsWorkflow
    from core.workflow import WorkflowSchema, NodeConfig
    from workflows.email_actions.email_actions_nodes import (
        IntentClassificationNode, ActionRouterNode, LogCallExtractionNode,
        EntityMatchingNode, UnknownActionNode
    )
    
    # Create test workflow
    class TestWorkflow(EmailActionsWorkflow):
        workflow_schema = WorkflowSchema(
            description="Test workflow",
            event_schema=EmailActionsEventSchema,
            start=IntentClassificationNode,
            nodes=[
                NodeConfig(node=IntentClassificationNode, connections=[ActionRouterNode]),
                NodeConfig(node=ActionRouterNode, connections=[LogCallExtractionNode], is_router=True),
                NodeConfig(node=LogCallExtractionNode, connections=[EntityMatchingNode]),
                NodeConfig(node=EntityMatchingNode, connections=[CreateStagingRecordTestingNode]),
                NodeConfig(node=CreateStagingRecordTestingNode, connections=[])
            ]
        )
    
    workflow = TestWorkflow()
    event = EmailActionsEventSchema(
        email_id=str(uuid4()),
        content="Log call with Dr. Smith about referrals",
        subject="Quick call",
        from_email="test@example.com"
    )
    
    result = workflow.run(event.model_dump())
    staging_node = result.nodes.get("CreateStagingRecordTestingNode", {})
    
    if staging_node.get("test_mode"):
        print("✅ Test mode confirmed - no database commits")
        simulated = staging_node.get("simulated_results", {})
        if simulated.get("staging_records"):
            print(f"Would create: {simulated}")


if __name__ == "__main__":
    from uuid import uuid4
    main()