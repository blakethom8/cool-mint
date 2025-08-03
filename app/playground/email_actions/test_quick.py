#!/usr/bin/env python3
"""
Quick test script for specific email action scenarios.
Useful for debugging and quick checks.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from workflows.email_actions.email_actions_workflow import EmailActionsWorkflow
from workflows.email_actions.email_actions_nodes import CreateStagingRecordTestingNode
from core.workflow import WorkflowSchema, NodeConfig
from schemas.email_actions_schema import EmailActionsEventSchema
from workflows.email_actions.email_actions_nodes import *


def quick_test(content, subject="Test Email", instruction=None, use_testing_node=True):
    """Quick test of email actions workflow"""
    
    from uuid import uuid4
    
    # Create event
    event = EmailActionsEventSchema(
        email_id=str(uuid4()),
        content=content,
        subject=subject,
        from_email="test@example.com",
        is_forwarded="Fwd:" in subject,
        user_instruction=instruction
    )
    
    # Choose workflow
    if use_testing_node:
        # Create custom workflow with testing node
        class TestWorkflow(EmailActionsWorkflow):
            workflow_schema = WorkflowSchema(
                description="Test workflow",
                event_schema=EmailActionsEventSchema,
                start=IntentClassificationNode,
                nodes=[
                    NodeConfig(node=IntentClassificationNode, connections=[ActionRouterNode]),
                    NodeConfig(node=ActionRouterNode, 
                             connections=[LogCallExtractionNode, AddNoteExtractionNode, 
                                        SetReminderExtractionNode, UnknownActionNode],
                             is_router=True),
                    NodeConfig(node=LogCallExtractionNode, connections=[EntityMatchingNode]),
                    NodeConfig(node=AddNoteExtractionNode, connections=[EntityMatchingNode]),
                    NodeConfig(node=SetReminderExtractionNode, connections=[EntityMatchingNode]),
                    NodeConfig(node=EntityMatchingNode, connections=[CreateStagingRecordTestingNode]),
                    NodeConfig(node=UnknownActionNode, connections=[]),
                    NodeConfig(node=CreateStagingRecordTestingNode, connections=[])
                ]
            )
        workflow = TestWorkflow()
        print("🧪 Using TESTING node (no DB commits)")
    else:
        workflow = EmailActionsWorkflow()
        print("⚠️  Using PRODUCTION workflow (will commit to DB)")
    
    print(f"\nSubject: {subject}")
    print(f"Content: {content[:100]}...")
    if instruction:
        print(f"Instruction: {instruction}")
    
    # Run workflow
    print("\nRunning workflow...")
    result = workflow.run(event.model_dump())
    
    # Display results
    classification = result.nodes.get("IntentClassificationNode", {})
    action_type = classification.get("action_type")
    confidence = classification.get("confidence_score", 0)
    
    print(f"\n✅ Classified as: {action_type} (confidence: {confidence:.2f})")
    
    # Show entity matching
    matching = result.nodes.get("EntityMatchingNode", {})
    if matching.get("entity_matching_complete"):
        print(f"\n📊 Entity Matching: {matching.get('match_status')}")
        results = matching.get("matching_results", {})
        
        for entity in results.get("entities", []):
            if entity.get("matched"):
                print(f"  ✓ {entity.get('name')} → {entity.get('match_display_name')}")
            else:
                print(f"  ✗ {entity.get('name')} (not found)")
    
    # Show staging result
    if use_testing_node:
        staging = result.nodes.get("CreateStagingRecordTestingNode", {})
        if staging.get("test_mode"):
            print(f"\n📝 Would create staging record (dry run)")
    else:
        staging = result.nodes.get("CreateStagingRecordNode", {})
        if staging.get("status") == "created":
            print(f"\n💾 Created staging record: {staging.get('email_action_id')}")
    
    return result


def test_entity_matching():
    """Test entity matching capabilities"""
    print("\n" + "="*70)
    print("ENTITY MATCHING TEST")
    print("="*70)
    
    # Test with known entities
    quick_test(
        "Had a meeting with Dr. DeStefano and Dr. Smith about referrals.",
        "Meeting notes",
        "Log this call"
    )
    
    # Test with unknown entities
    quick_test(
        "Dr. Unknown Person wants to join our program.",
        "New contact",
        "Add as note"
    )


def test_edge_cases():
    """Test edge cases"""
    print("\n" + "="*70)
    print("EDGE CASES TEST")
    print("="*70)
    
    # Very short content
    quick_test("Follow up", "Quick reminder")
    
    # No clear action
    quick_test("FYI - interesting article about healthcare", "FYI")
    
    # Multiple possible actions
    quick_test(
        "Log this call with Dr. Smith and remind me to follow up next week",
        "Call and reminder"
    )


def interactive_test():
    """Interactive test mode"""
    print("\n" + "="*70)
    print("INTERACTIVE TEST MODE")
    print("="*70)
    
    while True:
        print("\n" + "-"*40)
        content = input("Email content (or 'quit'): ").strip()
        if content.lower() == 'quit':
            break
        
        subject = input("Subject (optional): ").strip() or "Test Email"
        instruction = input("User instruction (optional): ").strip() or None
        
        use_test = input("Use test mode? (Y/n): ").strip().lower() != 'n'
        
        try:
            quick_test(content, subject, instruction, use_test)
        except Exception as e:
            print(f"\n❌ Error: {e}")


def test_from_sample_file():
    """Test using emails from sample_emails.json"""
    import json
    
    print("\n" + "="*70)
    print("TESTING WITH SAMPLE EMAILS")
    print("="*70)
    
    sample_file = Path(__file__).parent / "test_data" / "sample_emails.json"
    
    try:
        with open(sample_file, 'r') as f:
            emails = json.load(f)
        
        print(f"\nFound {len(emails)} emails in sample file")
        
        for i, email_data in enumerate(emails, 1):
            print(f"\n{'='*60}")
            print(f"Sample Email {i}/{len(emails)}")
            print(f"{'='*60}")
            print(f"ID: {email_data.get('id', 'N/A')}")
            print(f"Subject: {email_data.get('subject', 'N/A')}")
            print(f"From: {email_data.get('from_email', 'N/A')}")
            if email_data.get('user_instruction'):
                print(f"Instruction: {email_data.get('user_instruction')[:100]}...")
            
            quick_test(
                email_data.get('content', ''),
                email_data.get('subject', 'Sample Email'),
                email_data.get('user_instruction'),
                use_testing_node=True  # Default to test mode
            )
            
    except FileNotFoundError:
        print(f"❌ Sample file not found: {sample_file}")
    except json.JSONDecodeError:
        print(f"❌ Invalid JSON in sample file")
    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Quick email actions test")
    parser.add_argument("content", nargs="?", help="Email content to test")
    parser.add_argument("--subject", "-s", default="Test Email", help="Email subject")
    parser.add_argument("--instruction", "-i", help="User instruction")
    parser.add_argument("--production", "-p", action="store_true", 
                       help="Use production workflow (commits to DB)")
    parser.add_argument("--entity-test", action="store_true", 
                       help="Run entity matching tests")
    parser.add_argument("--edge-cases", action="store_true", 
                       help="Run edge case tests")
    parser.add_argument("--interactive", action="store_true", 
                       help="Interactive test mode")
    parser.add_argument("--sample-emails", action="store_true",
                       help="Test with emails from sample_emails.json")
    
    args = parser.parse_args()
    
    if args.interactive:
        interactive_test()
    elif args.entity_test:
        test_entity_matching()
    elif args.edge_cases:
        test_edge_cases()
    elif args.sample_emails:
        test_from_sample_file()
    elif args.content:
        quick_test(
            args.content,
            args.subject,
            args.instruction,
            not args.production
        )
    else:
        print("Usage examples:")
        print("  python test_quick.py 'Log call with Dr. Smith'")
        print("  python test_quick.py 'Remind me to follow up' -i 'Set reminder'")
        print("  python test_quick.py --interactive")
        print("  python test_quick.py --entity-test")
        print("  python test_quick.py --sample-emails")
        print("\nAdd --production to commit to database (use with caution!)")


if __name__ == "__main__":
    main()