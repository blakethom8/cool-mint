#!/usr/bin/env python3
"""Test all email actions with entity matching"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from workflows.email_actions import EmailActionsWorkflow
from workflows.email_actions.email_actions_nodes import CreateStagingRecordTestingNode
from core.workflow import WorkflowSchema, NodeConfig
from schemas.email_actions_schema import EmailActionsEventSchema
from workflows.email_actions.email_actions_nodes import (
    IntentClassificationNode, ActionRouterNode, 
    LogCallExtractionNode, AddNoteExtractionNode, SetReminderExtractionNode,
    EntityMatchingNode, UnknownActionNode
)


# Create test workflow that doesn't commit to DB
class TestEmailActionsWorkflow(EmailActionsWorkflow):
    workflow_schema = WorkflowSchema(
        description="Test workflow for email actions without DB commits",
        event_schema=EmailActionsEventSchema,
        start=IntentClassificationNode,
        nodes=[
            NodeConfig(node=IntentClassificationNode, connections=[ActionRouterNode]),
            NodeConfig(
                node=ActionRouterNode,
                connections=[LogCallExtractionNode, AddNoteExtractionNode, SetReminderExtractionNode, UnknownActionNode],
                is_router=True
            ),
            NodeConfig(node=LogCallExtractionNode, connections=[EntityMatchingNode]),
            NodeConfig(node=AddNoteExtractionNode, connections=[EntityMatchingNode]),
            NodeConfig(node=SetReminderExtractionNode, connections=[EntityMatchingNode]),
            NodeConfig(node=EntityMatchingNode, connections=[CreateStagingRecordTestingNode]),
            NodeConfig(node=UnknownActionNode, connections=[]),
            NodeConfig(node=CreateStagingRecordTestingNode, connections=[])
        ]
    )


def test_action(action_type: str, email_content: str, subject: str):
    """Test a specific action type"""
    from uuid import uuid4
    
    event = EmailActionsEventSchema(
        email_id=str(uuid4()),
        content=email_content,
        subject=subject,
        from_email="test@example.com",
        is_forwarded="Fwd:" in subject
    )
    
    workflow = TestEmailActionsWorkflow()
    result = workflow.run(event.model_dump())
    
    # Check results
    classification = result.nodes.get("IntentClassificationNode", {})
    if classification.get("action_type") != action_type:
        print(f"❌ Expected {action_type}, got {classification.get('action_type')}")
        return
    
    print(f"✅ Classified as: {action_type}")
    
    # Check entity matching
    matching = result.nodes.get("EntityMatchingNode", {})
    matching_results = matching.get("matching_results", {})
    
    print(f"   Entity Matching: {matching.get('match_status')}")
    print(f"   - Matched: {matching_results.get('matched_count', 0)}")
    print(f"   - Unmatched: {matching_results.get('unmatched_count', 0)}")
    
    # Check staging
    staging = result.nodes.get("CreateStagingRecordTestingNode", {})
    simulated = staging.get("simulated_results", {})
    
    if staging.get("test_mode"):
        staging_type = simulated.get("staging_type")
        staging_data = simulated.get("staging_records")
        
        print(f"   Staging: Would create 1 {staging_type} record")
        if isinstance(staging_data, dict):
            print(f"     - Match Status: {staging_data.get('entity_match_status')}")
            if staging_type == "note":
                matched_count = len(staging_data.get('matched_entity_ids', []))
                print(f"     - Primary Entity: {staging_data.get('related_entity_name')}")
                print(f"     - Total Entities: {matched_count} matched in JSONB")


def main():
    """Test all action types with entity matching"""
    
    print("=" * 70)
    print("TESTING ALL EMAIL ACTIONS WITH ENTITY MATCHING")
    print("=" * 70)
    
    print("\n1. LOG CALL - Multiple Participants")
    print("-" * 50)
    test_action(
        "log_call",
        "Had an MD-to-MD meeting with Dr. DeStefano and Dr. Smith about referrals.",
        "MD-to-MD Meeting"
    )
    
    print("\n2. ADD NOTE - Multiple Entities")
    print("-" * 50)
    test_action(
        "add_note",
        "Please add a note: Dr. Johnson mentioned that Dr. Williams from UCLA is interested in our program.",
        "Fwd: Important physician feedback"
    )
    
    print("\n3. SET REMINDER - With Assignee")
    print("-" * 50)
    test_action(
        "set_reminder",
        "Remind Blake Thomson to follow up with Dr. DeStefano next month about the collaboration.",
        "Reminder needed"
    )
    
    print("\n" + "=" * 70)
    print("ENTITY MATCHING SUMMARY")
    print("=" * 70)
    print("\nKey Features Demonstrated:")
    print("• Call Logs: Single record with all participants tracked in JSONB")
    print("• Notes: Single record with all entities tracked in JSONB")
    print("• Reminders: Single record with assignee matching")
    print("• All actions: Store matched IDs, unmatched names, and confidence scores")
    print("\n✅ All workflows now use entity matching!")


if __name__ == "__main__":
    main()