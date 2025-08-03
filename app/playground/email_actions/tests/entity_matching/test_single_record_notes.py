#!/usr/bin/env python3
"""Test that notes now create single records with all entities in JSONB"""

import sys
from pathlib import Path
import json

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from workflows.email_actions import EmailActionsWorkflow
from workflows.email_actions.email_actions_nodes import CreateStagingRecordTestingNode
from core.workflow import WorkflowSchema, NodeConfig
from schemas.email_actions_schema import EmailActionsEventSchema
from workflows.email_actions.email_actions_nodes import (
    IntentClassificationNode, ActionRouterNode, AddNoteExtractionNode,
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
            NodeConfig(node=ActionRouterNode, connections=[AddNoteExtractionNode], is_router=True),
            NodeConfig(node=AddNoteExtractionNode, connections=[EntityMatchingNode]),
            NodeConfig(node=EntityMatchingNode, connections=[CreateStagingRecordTestingNode]),
            NodeConfig(node=CreateStagingRecordTestingNode, connections=[])
        ]
    )


def test_note_with_multiple_entities():
    """Test that notes create a single record with all entities in JSONB"""
    from uuid import uuid4
    
    print("=" * 70)
    print("TESTING SINGLE RECORD PATTERN FOR NOTES")
    print("=" * 70)
    
    # Email with multiple entities
    event = EmailActionsEventSchema(
        email_id=str(uuid4()),
        content="""Please add this as a note.
        
        Had a productive meeting with Dr. DeStefano, Dr. Smith, and Dr. Johnson.
        They are all interested in our new referral program.
        
        Dr. Williams from UCLA also wants to join the initiative.
        """,
        subject="Fwd: Multiple physician interest",
        from_email="test@example.com",
        is_forwarded=True,
        user_instruction="Add this as a note"
    )
    
    workflow = TestWorkflow()
    result = workflow.run(event.model_dump())
    
    # Get staging results
    staging = result.nodes.get("CreateStagingRecordTestingNode", {})
    simulated = staging.get("simulated_results", {})
    staging_data = simulated.get("staging_records")
    
    print("\nWORKFLOW RESULTS:")
    print("-" * 50)
    
    if isinstance(staging_data, dict):
        print("✅ Single staging record created (as expected)")
        print(f"\nPrimary Entity:")
        print(f"  Name: {staging_data.get('related_entity_name')}")
        print(f"  ID: {staging_data.get('related_entity_id')}")
        print(f"  Type: {staging_data.get('related_entity_type')}")
        
        print(f"\nAll Matched Entities (in JSONB):")
        for entity in staging_data.get('matched_entity_ids', []):
            print(f"  - {entity.get('name')} (ID: {entity.get('id')})")
            print(f"    Confidence: {entity.get('confidence')}")
        
        print(f"\nUnmatched Entities (in JSONB):")
        for entity in staging_data.get('unmatched_entities', []):
            print(f"  - {entity.get('name')} ({entity.get('reason')})")
        
        print(f"\nEntity Match Status: {staging_data.get('entity_match_status')}")
        print(f"Topics: {staging_data.get('llm_topics')}")
        print(f"Sentiment: {staging_data.get('llm_sentiment')}")
        
        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print("• Notes now create ONE staging record per email")
        print("• All entities are captured in matched_entity_ids JSONB field")
        print("• Primary entity is set in related_entity_* fields")
        print("• This matches the pattern used by Call Logs")
        print("• Simplifies approval process (one approval per email)")
        
    else:
        print("❌ Unexpected result - not a single dict")
        print(f"Got: {type(staging_data)}")


if __name__ == "__main__":
    test_note_with_multiple_entities()