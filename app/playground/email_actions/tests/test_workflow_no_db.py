#!/usr/bin/env python3
"""Test email actions workflow without database commits"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import the workflow components
from workflows.email_actions import EmailActionsWorkflow
from workflows.email_actions.email_actions_nodes import (
    IntentClassificationNode,
    ActionRouterNode,
    LogCallExtractionNode,
    AddNoteExtractionNode,
    SetReminderExtractionNode,
    UnknownActionNode,
    EntityMatchingNode,
    CreateStagingRecordTestingNode  # Use testing node instead
)
from core.workflow import WorkflowSchema, NodeConfig
from schemas.email_actions_schema import EmailActionsEventSchema


# Create a custom workflow that uses the testing node
class TestEmailActionsWorkflow(EmailActionsWorkflow):
    """Test workflow that doesn't commit to database"""
    
    workflow_schema = WorkflowSchema(
        description="Test workflow for email actions without DB commits",
        event_schema=EmailActionsEventSchema,
        start=IntentClassificationNode,
        nodes=[
            NodeConfig(
                node=IntentClassificationNode,
                connections=[ActionRouterNode],
                description="Classify email intent into action types"
            ),
            NodeConfig(
                node=ActionRouterNode,
                connections=[
                    LogCallExtractionNode,
                    AddNoteExtractionNode,
                    SetReminderExtractionNode,
                    UnknownActionNode
                ],
                is_router=True,
                description="Route to appropriate extraction node"
            ),
            NodeConfig(
                node=LogCallExtractionNode,
                connections=[EntityMatchingNode],
                description="Extract call/meeting log parameters"
            ),
            NodeConfig(
                node=AddNoteExtractionNode,
                connections=[EntityMatchingNode],
                description="Extract note parameters"
            ),
            NodeConfig(
                node=SetReminderExtractionNode,
                connections=[EntityMatchingNode],  # Now routes through entity matching
                description="Extract reminder parameters"
            ),
            NodeConfig(
                node=EntityMatchingNode,
                connections=[CreateStagingRecordTestingNode],  # Use testing node
                description="Match extracted entities to database records"
            ),
            NodeConfig(
                node=UnknownActionNode,
                connections=[],  # Terminal node
                description="Handle unknown action types"
            ),
            NodeConfig(
                node=CreateStagingRecordTestingNode,  # Testing node
                connections=[],  # Terminal node
                description="Simulate staging record creation (no DB commit)"
            ),
        ]
    )


def test_workflow(email_content: str, subject: str = "Test Email", user_instruction: str = None):
    """Test the workflow without database commits"""
    
    print("=" * 60)
    print("Testing Email Actions Workflow (No DB Commits)")
    print("=" * 60)
    
    # Create test event
    from uuid import uuid4
    event = EmailActionsEventSchema(
        email_id=str(uuid4()),
        content=email_content,
        subject=subject,
        from_email="test@example.com",
        is_forwarded=True if "Fwd:" in subject else False,
        user_instruction=user_instruction
    )
    
    print(f"\nTest Email:")
    print(f"Subject: {event.subject}")
    print(f"From: {event.from_email}")
    print(f"Content: {event.content[:100]}...")
    if event.user_instruction:
        print(f"User Instruction: {event.user_instruction}")
    
    # Run test workflow
    workflow = TestEmailActionsWorkflow()
    result = workflow.run(event.model_dump())
    
    # Display results
    print("\n" + "=" * 60)
    print("WORKFLOW RESULTS")
    print("=" * 60)
    
    # Check each node's results
    for node_name, node_data in result.nodes.items():
        print(f"\n[{node_name}]")
        
        if node_name == "IntentClassificationNode":
            print(f"  Action Type: {node_data.get('action_type')}")
            print(f"  Confidence: {node_data.get('confidence_score')}")
            
        elif node_name == "AddNoteExtractionNode":
            params = node_data.get("note_parameters", {})
            print(f"  Note Type: {params.get('note_type')}")
            print(f"  Topics: {params.get('topics')}")
            print(f"  Sentiment: {params.get('sentiment')}")
            print(f"  Entities: {len(params.get('mentioned_entities', []))}")
            
        elif node_name == "EntityMatchingNode":
            print(f"  Match Status: {node_data.get('match_status')}")
            results = node_data.get('matching_results', {})
            print(f"  Matched: {results.get('matched_count', 0)}")
            print(f"  Unmatched: {results.get('unmatched_count', 0)}")
            
        elif node_name == "CreateStagingRecordTestingNode":
            print(f"  Status: {node_data.get('status')}")
            print(f"  Test Mode: {node_data.get('test_mode')}")
            print(f"  Action Type: {node_data.get('action_type')}")
            
            # Show what would have been created
            simulated = node_data.get('simulated_results', {})
            if simulated:
                print(f"\n  [SIMULATED DATABASE OPERATIONS]")
                print(f"  Would create EmailAction: {simulated.get('email_action', {}).get('id')}")
                
                staging_data = simulated.get('staging_records')
                if isinstance(staging_data, list):
                    print(f"  Would create {len(staging_data)} staging records")
                    for i, record in enumerate(staging_data[:3]):  # Show first 3
                        print(f"    - Record {i+1}: {record.get('related_entity_name', 'N/A')}")
                elif staging_data:
                    print(f"  Would create 1 staging record")
    
    return result


def main():
    """Run test examples"""
    
    # Test 1: Note with multiple entities
    print("\n\nTEST 1: Add Note with Multiple Entities")
    print("-" * 60)
    
    test_workflow(
        email_content="""Please add this as a note.
        
        Had a great meeting with Dr. DeStefano from Cedar Sinai. 
        She mentioned that Dr. Smith is interested in our new referral program.
        
        Key points:
        - Both doctors are excited about the collaboration
        - Planning follow-up next month
        - High potential for increased referrals
        """,
        subject="Fwd: Meeting Notes - Referral Program",
        user_instruction="Please add this as a note"
    )
    
    # Test 2: Call log
    print("\n\nTEST 2: Log Call")
    print("-" * 60)
    
    test_workflow(
        email_content="""Log a call with Dr. Johnson and Dr. Williams.
        
        Discussed the new treatment protocols. 
        Meeting lasted about 45 minutes.
        Very productive discussion about patient care improvements.
        """,
        subject="Call with Johnson and Williams",
        user_instruction="Log this call"
    )
    
    # Test 3: Set reminder
    print("\n\nTEST 3: Set Reminder")
    print("-" * 60)
    
    test_workflow(
        email_content="""Remind me to follow up with the cardiology department next week about the referral metrics report.""",
        subject="Reminder needed",
        user_instruction="Set a reminder"
    )


if __name__ == "__main__":
    main()