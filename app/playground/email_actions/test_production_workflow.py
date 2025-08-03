#!/usr/bin/env python3
"""
Main test script for email actions workflow using production configuration.
This script WILL commit to the database - use with caution!
"""

import sys
from pathlib import Path
from datetime import datetime
import json

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from database.session import db_session
from database.data_models.email_actions import EmailAction, CallLogStaging, NoteStaging, ReminderStaging
from workflows.email_actions.email_actions_workflow import EmailActionsWorkflow
from schemas.email_actions_schema import EmailActionsEventSchema


class ProductionWorkflowTester:
    """Test the production email actions workflow"""
    
    def __init__(self):
        self.workflow = EmailActionsWorkflow()
        self.results = []
    
    def test_call_log(self):
        """Test call log with entity matching"""
        print("\n" + "="*60)
        print("TEST: Call Log with Multiple Participants")
        print("="*60)
        
        from uuid import uuid4
        event = EmailActionsEventSchema(
            email_id=str(uuid4()),
            content="""Log this MD-to-MD meeting with Dr. DeStefano and Dr. Smith.
            
            Discussed referral patterns and collaboration opportunities.
            Very productive 45-minute discussion about improving patient care.
            """,
            subject="MD-to-MD Meeting Notes",
            from_email="test@example.com",
            user_instruction="Log this call"
        )
        
        result = self.workflow.run(event.model_dump())
        self._display_results(result, "log_call")
        return result
    
    def test_add_note(self):
        """Test note creation with entity matching"""
        print("\n" + "="*60)
        print("TEST: Add Note with Multiple Entities")
        print("="*60)
        
        from uuid import uuid4
        event = EmailActionsEventSchema(
            email_id=str(uuid4()),
            content="""Please add this as a note.
            
            Dr. Johnson from Cedar Sinai mentioned that Dr. Williams is very interested 
            in our new referral tracking program. Both physicians want to participate 
            in the pilot program starting next month.
            
            This is a great opportunity for expanding our network.
            """,
            subject="Fwd: Physician Interest in Referral Program",
            from_email="test@example.com",
            is_forwarded=True,
            user_instruction="Add this as a note"
        )
        
        result = self.workflow.run(event.model_dump())
        self._display_results(result, "add_note")
        return result
    
    def test_set_reminder(self):
        """Test reminder creation with entity matching"""
        print("\n" + "="*60)
        print("TEST: Set Reminder with Entity Matching")
        print("="*60)
        
        from uuid import uuid4
        event = EmailActionsEventSchema(
            email_id=str(uuid4()),
            content="""Remind me to follow up with Dr. DeStefano in 30 days about the 
            referral program results. Need to check metrics and gather feedback.""",
            subject="Follow-up reminder needed",
            from_email="test@example.com",
            user_instruction="Set a reminder"
        )
        
        result = self.workflow.run(event.model_dump())
        self._display_results(result, "set_reminder")
        return result
    
    def _display_results(self, result, expected_action):
        """Display workflow results and database records"""
        
        # Classification results
        classification = result.nodes.get("IntentClassificationNode", {})
        action_type = classification.get("action_type")
        confidence = classification.get("confidence_score", 0)
        
        print(f"\nClassification:")
        print(f"  Action: {action_type} (confidence: {confidence:.2f})")
        
        if action_type != expected_action:
            print(f"  ⚠️  Expected {expected_action}, got {action_type}")
            return
        
        # Entity matching results
        matching = result.nodes.get("EntityMatchingNode", {})
        match_results = matching.get("matching_results", {})
        
        print(f"\nEntity Matching:")
        print(f"  Status: {matching.get('match_status')}")
        print(f"  Matched: {match_results.get('matched_count', 0)}")
        print(f"  Unmatched: {match_results.get('unmatched_count', 0)}")
        
        # Staging record results
        staging_node = result.nodes.get("CreateStagingRecordNode", {})
        if staging_node.get("status") == "created":
            email_action_id = staging_node.get("email_action_id")
            print(f"\n✅ Staging record created")
            print(f"  Email Action ID: {email_action_id}")
            
            # Query database for details
            self._query_staging_records(email_action_id, action_type)
        else:
            print(f"\n❌ Failed to create staging record: {staging_node.get('error')}")
    
    def _query_staging_records(self, email_action_id, action_type):
        """Query and display staging records from database"""
        
        for session in db_session():
            if action_type == "log_call":
                staging = session.query(CallLogStaging).filter_by(
                    email_action_id=email_action_id
                ).first()
                
                if staging:
                    print(f"\n  Call Log Staging:")
                    print(f"    Subject: {staging.subject}")
                    print(f"    Participants: {len(staging.matched_participant_ids or [])}")
                    print(f"    Match Status: {staging.entity_match_status}")
                    
            elif action_type == "add_note":
                staging = session.query(NoteStaging).filter_by(
                    email_action_id=email_action_id
                ).first()
                
                if staging:
                    print(f"\n  Note Staging:")
                    print(f"    Primary Entity: {staging.related_entity_name}")
                    print(f"    Total Entities: {len(staging.matched_entity_ids or [])}")
                    print(f"    Topics: {staging.llm_topics}")
                    print(f"    Sentiment: {staging.llm_sentiment}")
                    print(f"    Match Status: {staging.entity_match_status}")
                    
            elif action_type == "set_reminder":
                staging = session.query(ReminderStaging).filter_by(
                    email_action_id=email_action_id
                ).first()
                
                if staging:
                    print(f"\n  Reminder Staging:")
                    print(f"    Text: {staging.reminder_text[:50]}...")
                    print(f"    Due Date: {staging.due_date}")
                    print(f"    Assignee: {staging.assignee}")
                    print(f"    Match Status: {staging.entity_match_status}")
            
            break
    
    def test_sample_emails(self, skip_confirmation=False):
        """Test with emails from sample_emails.json"""
        import json
        
        sample_file = Path(__file__).parent / "test_data" / "sample_emails.json"
        
        try:
            with open(sample_file, 'r') as f:
                emails = json.load(f)
            
            print(f"\n📧 Found {len(emails)} emails in sample file")
            
            if not skip_confirmation:
                print("\n⚠️  WARNING: This will create records in the database!")
                response = input("\nContinue? (y/N): ")
                if response.lower() != 'y':
                    print("Cancelled.")
                    return
            
            for i, email_data in enumerate(emails, 1):
                print(f"\n{'='*60}")
                print(f"Sample Email {i}/{len(emails)}")
                print(f"{'='*60}")
                print(f"Subject: {email_data.get('subject', 'N/A')}")
                
                event = EmailActionsEventSchema(
                    email_id=email_data.get('id', str(uuid4())),
                    content=email_data.get('content', ''),
                    subject=email_data.get('subject', 'Sample Email'),
                    from_email=email_data.get('from_email', 'test@example.com'),
                    is_forwarded=email_data.get('is_forwarded', 'Fwd:' in email_data.get('subject', '')),
                    user_instruction=email_data.get('user_instruction')
                )
                
                result = self.workflow.run(event.model_dump())
                
                # Determine expected action from instruction or content
                expected_action = None
                instruction = (email_data.get('user_instruction') or '').lower()
                if 'log' in instruction and ('call' in instruction or 'md-to-md' in instruction):
                    expected_action = 'log_call'
                elif 'note' in instruction or 'add' in instruction:
                    expected_action = 'add_note'
                elif 'remind' in instruction:
                    expected_action = 'set_reminder'
                
                self._display_results(result, expected_action)
                
        except FileNotFoundError:
            print(f"❌ Sample file not found: {sample_file}")
        except json.JSONDecodeError:
            print(f"❌ Invalid JSON in sample file")
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    def run_all_tests(self):
        """Run all workflow tests"""
        print("\n" + "="*70)
        print("PRODUCTION WORKFLOW TESTS - WITH DATABASE COMMITS")
        print("="*70)
        print("\n⚠️  WARNING: This will create records in the database!")
        
        response = input("\nContinue? (y/N): ")
        if response.lower() != 'y':
            print("Cancelled.")
            return
        
        try:
            self.test_call_log()
            self.test_add_note()
            self.test_set_reminder()
            
            print("\n" + "="*70)
            print("SUMMARY")
            print("="*70)
            print("✅ All tests completed successfully")
            print("✅ Records created in database staging tables")
            print("\nNext steps:")
            print("1. Check staging tables for created records")
            print("2. Approve/reject staging records as needed")
            print("3. Transfer approved records to production tables")
            
        except Exception as e:
            print(f"\n❌ Error during testing: {e}")
            import traceback
            traceback.print_exc()


def main():
    """Main entry point"""
    import argparse
    from uuid import uuid4
    
    parser = argparse.ArgumentParser(description="Test production email actions workflow")
    parser.add_argument("--test", choices=["call", "note", "reminder", "all"], 
                       default="all", help="Which test to run")
    parser.add_argument("--skip-confirmation", action="store_true", 
                       help="Skip confirmation prompt (use with caution!)")
    parser.add_argument("--sample-emails", action="store_true",
                       help="Test with emails from sample_emails.json")
    
    args = parser.parse_args()
    
    tester = ProductionWorkflowTester()
    
    if args.sample_emails:
        tester.test_sample_emails(args.skip_confirmation)
    elif args.test == "all":
        if args.skip_confirmation:
            # Bypass confirmation for automated testing
            tester.test_call_log()
            tester.test_add_note()
            tester.test_set_reminder()
        else:
            tester.run_all_tests()
    elif args.test == "call":
        tester.test_call_log()
    elif args.test == "note":
        tester.test_add_note()
    elif args.test == "reminder":
        tester.test_set_reminder()


if __name__ == "__main__":
    main()