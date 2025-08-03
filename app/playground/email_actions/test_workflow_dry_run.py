#!/usr/bin/env python3
"""
Test email actions workflow WITHOUT database commits (dry run).
Uses the testing node to simulate database operations.
"""

import sys
from pathlib import Path
from datetime import datetime
import json

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from workflows.email_actions import EmailActionsWorkflow
from workflows.email_actions.email_actions_nodes import (
    IntentClassificationNode, ActionRouterNode,
    LogCallExtractionNode, AddNoteExtractionNode, SetReminderExtractionNode,
    EntityMatchingNode, UnknownActionNode, CreateStagingRecordTestingNode
)
from core.workflow import WorkflowSchema, NodeConfig
from schemas.email_actions_schema import EmailActionsEventSchema


class DryRunWorkflow(EmailActionsWorkflow):
    """Email actions workflow with testing node (no DB commits)"""
    
    workflow_schema = WorkflowSchema(
        description="Email actions workflow - dry run mode",
        event_schema=EmailActionsEventSchema,
        start=IntentClassificationNode,
        nodes=[
            NodeConfig(
                node=IntentClassificationNode,
                connections=[ActionRouterNode],
                description="Classify email intent"
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
                description="Route to extraction node"
            ),
            NodeConfig(
                node=LogCallExtractionNode,
                connections=[EntityMatchingNode],
                description="Extract call log data"
            ),
            NodeConfig(
                node=AddNoteExtractionNode,
                connections=[EntityMatchingNode],
                description="Extract note data"
            ),
            NodeConfig(
                node=SetReminderExtractionNode,
                connections=[EntityMatchingNode],
                description="Extract reminder data"
            ),
            NodeConfig(
                node=EntityMatchingNode,
                connections=[CreateStagingRecordTestingNode],
                description="Match entities"
            ),
            NodeConfig(
                node=UnknownActionNode,
                connections=[],
                description="Handle unknown actions"
            ),
            NodeConfig(
                node=CreateStagingRecordTestingNode,  # Testing node - no DB commit
                connections=[],
                description="Simulate staging record creation"
            ),
        ]
    )


class DryRunTester:
    """Test workflow without database commits"""
    
    def __init__(self):
        self.workflow = DryRunWorkflow()
        self.test_cases = []
    
    def add_test_case(self, name, content, subject, user_instruction=None, is_forwarded=False):
        """Add a test case"""
        self.test_cases.append({
            "name": name,
            "content": content,
            "subject": subject,
            "user_instruction": user_instruction,
            "is_forwarded": is_forwarded
        })
    
    def run_test(self, test_case):
        """Run a single test case"""
        from uuid import uuid4
        
        print(f"\n{'='*60}")
        print(f"TEST: {test_case['name']}")
        print(f"{'='*60}")
        
        event = EmailActionsEventSchema(
            email_id=str(uuid4()),
            content=test_case["content"],
            subject=test_case["subject"],
            from_email="test@example.com",
            is_forwarded=test_case["is_forwarded"],
            user_instruction=test_case.get("user_instruction")
        )
        
        print(f"Subject: {event.subject}")
        if event.user_instruction:
            print(f"Instruction: {event.user_instruction}")
        
        # Run workflow
        result = self.workflow.run(event.model_dump())
        
        # Display results
        self._display_results(result)
        
        return result
    
    def _display_results(self, result):
        """Display workflow results"""
        
        # Classification
        classification = result.nodes.get("IntentClassificationNode", {})
        print(f"\nClassification:")
        print(f"  Action: {classification.get('action_type')}")
        print(f"  Confidence: {classification.get('confidence_score', 0):.2f}")
        
        # Extraction details
        action_type = classification.get("action_type")
        if action_type == "log_call":
            extraction = result.nodes.get("LogCallExtractionNode", {})
            params = extraction.get("call_log_parameters", {})
            print(f"\nExtracted Data:")
            print(f"  Subject: {params.get('subject')}")
            print(f"  Activity Type: {params.get('activity_type')}")
            print(f"  Participants: {len(params.get('participants', []))}")
            
        elif action_type == "add_note":
            extraction = result.nodes.get("AddNoteExtractionNode", {})
            params = extraction.get("note_parameters", {})
            print(f"\nExtracted Data:")
            print(f"  Note Type: {params.get('note_type')}")
            print(f"  Topics: {params.get('topics')}")
            print(f"  Sentiment: {params.get('sentiment')}")
            print(f"  Entities: {len(params.get('mentioned_entities', []))}")
            
        elif action_type == "set_reminder":
            extraction = result.nodes.get("SetReminderExtractionNode", {})
            params = extraction.get("reminder_parameters", {})
            print(f"\nExtracted Data:")
            print(f"  Reminder: {params.get('reminder_text', '')[:50]}...")
            print(f"  Due Date: {params.get('due_date')}")
            print(f"  Assignee: {params.get('assignee')}")
        
        # Entity matching
        matching = result.nodes.get("EntityMatchingNode", {})
        if matching.get("entity_matching_complete"):
            print(f"\nEntity Matching:")
            print(f"  Status: {matching.get('match_status')}")
            results = matching.get("matching_results", {})
            print(f"  Matched: {results.get('matched_count', 0)}")
            print(f"  Unmatched: {results.get('unmatched_count', 0)}")
        
        # Staging simulation
        staging = result.nodes.get("CreateStagingRecordTestingNode", {})
        if staging.get("test_mode"):
            print(f"\nStaging Simulation:")
            print(f"  Status: {staging.get('status')}")
            
            simulated = staging.get("simulated_results", {})
            staging_type = simulated.get("staging_type")
            staging_data = simulated.get("staging_records")
            
            if isinstance(staging_data, dict):
                print(f"  Would create 1 {staging_type} staging record")
                print(f"  Match Status: {staging_data.get('entity_match_status')}")
                
                if staging_type == "note":
                    print(f"  Primary Entity: {staging_data.get('related_entity_name')}")
                    print(f"  Total Entities in JSONB: {len(staging_data.get('matched_entity_ids', []))}")
                elif staging_type == "call_log":
                    print(f"  Participants in JSONB: {len(staging_data.get('matched_participant_ids', []))}")
    
    def run_all_tests(self):
        """Run all test cases"""
        
        print("\n" + "="*70)
        print("DRY RUN WORKFLOW TESTS - NO DATABASE COMMITS")
        print("="*70)
        print("\n✅ Safe to run - no database changes will be made")
        
        # Load standard test cases
        self._load_standard_tests()
        
        # Run each test
        results = []
        for test_case in self.test_cases:
            try:
                result = self.run_test(test_case)
                results.append((test_case["name"], "Success"))
            except Exception as e:
                results.append((test_case["name"], f"Failed: {e}"))
                print(f"\n❌ Test failed: {e}")
        
        # Summary
        print("\n" + "="*70)
        print("SUMMARY")
        print("="*70)
        
        success_count = sum(1 for _, status in results if status == "Success")
        print(f"Tests run: {len(results)}")
        print(f"Successful: {success_count}")
        print(f"Failed: {len(results) - success_count}")
        
        if success_count == len(results):
            print("\n✅ All tests passed!")
        
        print("\nNo database changes were made.")
    
    def load_sample_emails(self):
        """Load emails from sample_emails.json"""
        import json
        
        sample_file = Path(__file__).parent / "test_data" / "sample_emails.json"
        
        try:
            with open(sample_file, 'r') as f:
                emails = json.load(f)
            
            for email in emails:
                self.add_test_case(
                    f"Sample: {email.get('subject', 'Unknown')}",
                    email.get('content', ''),
                    email.get('subject', 'Sample Email'),
                    email.get('user_instruction'),
                    email.get('is_forwarded', False)
                )
            
            print(f"📧 Loaded {len(emails)} emails from sample file")
            return True
            
        except Exception as e:
            print(f"⚠️  Could not load sample emails: {e}")
            return False
    
    def _load_standard_tests(self):
        """Load standard test cases"""
        
        # Call log tests
        self.add_test_case(
            "Call Log - MD to MD",
            """Log this MD-to-MD lunch meeting with Dr. DeStefano.
            Discussed new referral patterns and collaboration opportunities.
            Meeting lasted 45 minutes.""",
            "MD-to-MD Lunch with Dr. DeStefano",
            "Log this call"
        )
        
        self.add_test_case(
            "Call Log - Multiple Participants",
            """Had a virtual meeting with Dr. Smith, Dr. Johnson, and Dr. Williams.
            Topics: treatment protocols, research collaboration.
            Very productive discussion.""",
            "Team meeting notes"
        )
        
        # Note tests
        self.add_test_case(
            "Note - Single Entity",
            """Dr. McDonald mentioned interest in the referral program.
            Very enthusiastic about participating.""",
            "Fwd: Physician feedback",
            "Add as note",
            is_forwarded=True
        )
        
        self.add_test_case(
            "Note - Multiple Entities",
            """Important update: Dr. DeStefano and Dr. Smith from Cedar Sinai 
            are both interested in joining our pilot program. 
            Dr. Johnson from UCLA also expressed interest.""",
            "Fwd: Multiple physician interest",
            "Please add this as a note",
            is_forwarded=True
        )
        
        # Reminder tests
        self.add_test_case(
            "Reminder - Simple",
            "Remind me to follow up with Dr. DeStefano next month",
            "Follow-up needed",
            "Set reminder"
        )
        
        self.add_test_case(
            "Reminder - Detailed",
            """Set a reminder for Blake Thomson to prepare the quarterly report 
            for UCLA Medical Center by end of month. Include metrics and goals.""",
            "Task: Quarterly report"
        )


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test workflow without DB commits")
    parser.add_argument("--verbose", "-v", action="store_true", 
                       help="Show detailed output")
    parser.add_argument("--test", type=str,
                       help="Run specific test by name")
    parser.add_argument("--sample-emails", action="store_true",
                       help="Test with emails from sample_emails.json")
    parser.add_argument("--include-samples", action="store_true",
                       help="Include sample emails with standard tests")
    
    args = parser.parse_args()
    
    tester = DryRunTester()
    
    if args.sample_emails:
        # Only run sample emails
        if tester.load_sample_emails():
            tester.run_all_tests()
    elif args.test:
        # Run specific test
        tester._load_standard_tests()
        if args.include_samples:
            tester.load_sample_emails()
        test = next((t for t in tester.test_cases if args.test.lower() in t["name"].lower()), None)
        if test:
            tester.run_test(test)
        else:
            print(f"Test '{args.test}' not found")
            print("\nAvailable tests:")
            for t in tester.test_cases:
                print(f"  - {t['name']}")
    else:
        # Run all tests
        if args.include_samples:
            # Load both standard and sample tests
            tester._load_standard_tests()
            tester.load_sample_emails()
        tester.run_all_tests()


if __name__ == "__main__":
    main()