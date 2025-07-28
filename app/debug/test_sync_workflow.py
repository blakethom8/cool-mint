#!/usr/bin/env python3
"""
Phase 1: Synchronous Test Script for Core Email Workflow Functionality
Tests email sync and workflow execution without Celery
"""
import os
import sys
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

# Set up Django settings if needed
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')

from database.session import db_session
from database.data_models.email_data import Email
from database.data_models.email_actions import EmailAction
from services.email_service import EmailService
from core.workflow import WorkflowEngine
from workflows.workflow_registry import WorkflowRegistry
from schemas.email_actions_schema import EmailActionsEventSchema


class SyncWorkflowTester:
    """Test email workflow functionality synchronously"""
    
    def __init__(self):
        self.results = {
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "errors": []
        }
    
    def test_database_connection(self):
        """Test 1: Verify database connection"""
        print("\n🔍 Test 1: Database Connection")
        print("-" * 50)
        
        try:
            with next(db_session()) as db:
                # Try a simple query
                count = db.query(Email).count()
                print(f"✅ Database connected successfully")
                print(f"   Total emails in database: {count}")
                self.results["tests_passed"] += 1
                return True
        except Exception as e:
            print(f"❌ Database connection failed: {str(e)}")
            self.results["errors"].append(f"Database: {str(e)}")
            self.results["tests_failed"] += 1
            return False
        finally:
            self.results["tests_run"] += 1
    
    def test_email_service_list(self):
        """Test 2: Test EmailService list functionality"""
        print("\n🔍 Test 2: Email Service - List Emails")
        print("-" * 50)
        
        try:
            with next(db_session()) as db:
                service = EmailService(db)
                emails, total = service.list_emails(page=1, page_size=5)
                
                print(f"✅ Email service working")
                print(f"   Found {total} total emails")
                print(f"   Retrieved {len(emails)} emails for page 1")
                
                if emails:
                    print("\n   Sample email:")
                    email = emails[0]
                    print(f"   - ID: {email['id']}")
                    print(f"   - Subject: {email['subject']}")
                    print(f"   - From: {email['from_email']}")
                    print(f"   - Processed: {email['processed']}")
                
                self.results["tests_passed"] += 1
                return emails
        except Exception as e:
            print(f"❌ Email service failed: {str(e)}")
            self.results["errors"].append(f"EmailService: {str(e)}")
            self.results["tests_failed"] += 1
            return []
        finally:
            self.results["tests_run"] += 1
    
    def test_workflow_direct(self, email_id: Optional[str] = None):
        """Test 3: Test EMAIL_ACTIONS workflow directly without Celery"""
        print("\n🔍 Test 3: Direct Workflow Execution")
        print("-" * 50)
        
        try:
            with next(db_session()) as db:
                # Get an email to process
                if not email_id:
                    # Find first unprocessed email
                    email = db.query(Email).filter(
                        Email.processed == False
                    ).first()
                    
                    if not email:
                        # Just get the most recent email
                        email = db.query(Email).order_by(Email.date.desc()).first()
                else:
                    email = db.query(Email).filter(Email.id == email_id).first()
                
                if not email:
                    print("❌ No emails found to test workflow")
                    self.results["tests_failed"] += 1
                    return None
                
                print(f"📧 Testing with email:")
                print(f"   - ID: {email.id}")
                print(f"   - Subject: {email.subject}")
                print(f"   - From: {email.from_email}")
                
                # Create event data
                event_data = {
                    "email_id": str(email.id),
                    "content": email.body or email.body_plain or '',
                    "subject": email.subject or '',
                    "from_email": email.from_email or 'unknown',
                    "is_forwarded": email.is_forwarded or False,
                    "user_instruction": email.user_instruction
                }
                
                print("\n🚀 Running EMAIL_ACTIONS workflow...")
                
                # Get workflow and run it
                workflow = WorkflowRegistry.EMAIL_ACTIONS.value()
                engine = WorkflowEngine()
                
                # Create event schema
                event_schema = EmailActionsEventSchema(**event_data)
                
                # Run workflow
                result = engine.run(workflow, event_schema.dict())
                
                print("✅ Workflow executed successfully!")
                
                # Check if action was created
                action = db.query(EmailAction).filter(
                    EmailAction.email_id == str(email.id)
                ).order_by(EmailAction.created_at.desc()).first()
                
                if action:
                    print(f"\n📝 Email Action created:")
                    print(f"   - Type: {action.action_type}")
                    print(f"   - Status: {action.status}")
                    print(f"   - Confidence: {action.confidence_score}")
                    print(f"   - Reasoning: {action.reasoning[:100]}...")
                else:
                    print("\n⚠️  No action created (email might not contain actionable content)")
                
                self.results["tests_passed"] += 1
                return result
                
        except Exception as e:
            print(f"❌ Workflow execution failed: {str(e)}")
            import traceback
            traceback.print_exc()
            self.results["errors"].append(f"Workflow: {str(e)}")
            self.results["tests_failed"] += 1
            return None
        finally:
            self.results["tests_run"] += 1
    
    def test_nylas_sync(self):
        """Test 4: Test Nylas sync functionality"""
        print("\n🔍 Test 4: Nylas Email Sync")
        print("-" * 50)
        
        try:
            # Check if Nylas credentials are configured
            if not os.environ.get("NYLAS_API_KEY"):
                print("⚠️  NYLAS_API_KEY not configured - skipping sync test")
                return None
            
            from services.email_sync_manager import EmailSyncManager
            
            sync_manager = EmailSyncManager()
            print("📥 Attempting to sync emails from last 30 minutes...")
            
            result = sync_manager.sync_recent_emails(
                minutes_back=30,
                limit=5,
                process_emails=False  # Don't trigger processing
            )
            
            print(f"✅ Sync completed successfully!")
            print(f"   - Total fetched: {result['total_fetched']}")
            print(f"   - New emails: {result['new_emails']}")
            print(f"   - Updated emails: {result['updated_emails']}")
            print(f"   - Sync mode: {result['sync_mode']}")
            
            self.results["tests_passed"] += 1
            return result
            
        except Exception as e:
            print(f"❌ Nylas sync failed: {str(e)}")
            self.results["errors"].append(f"Nylas: {str(e)}")
            self.results["tests_failed"] += 1
            return None
        finally:
            self.results["tests_run"] += 1
    
    def run_all_tests(self):
        """Run all synchronous tests"""
        print("=" * 60)
        print("🧪 SYNCHRONOUS EMAIL WORKFLOW TESTS")
        print("=" * 60)
        
        # Test 1: Database
        if not self.test_database_connection():
            print("\n⛔ Database connection failed - stopping tests")
            return self.print_summary()
        
        # Test 2: Email Service
        emails = self.test_email_service_list()
        
        # Test 3: Workflow
        if emails:
            self.test_workflow_direct()
        
        # Test 4: Nylas Sync
        self.test_nylas_sync()
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"Tests Run:    {self.results['tests_run']}")
        print(f"Tests Passed: {self.results['tests_passed']} ✅")
        print(f"Tests Failed: {self.results['tests_failed']} ❌")
        
        if self.results["errors"]:
            print("\n❌ Errors encountered:")
            for error in self.results["errors"]:
                print(f"   - {error}")
        
        print("\n" + "=" * 60)
        
        return self.results


def main():
    """Run synchronous tests"""
    tester = SyncWorkflowTester()
    tester.run_all_tests()


if __name__ == "__main__":
    main()