#!/usr/bin/env python3
"""
Phase 3: Full Async Email Processing Workflow Test
Tests the complete end-to-end async email processing with Celery
"""
import os
import sys
import time
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from database.session import db_session
from database.data_models.email_data import Email
from database.data_models.email_actions import EmailAction
from database.event import Event
from worker.config import celery_app


class AsyncWorkflowTester:
    """Test full async email workflow"""
    
    def __init__(self, api_base_url: str = "http://localhost:8080"):
        self.api_base_url = api_base_url
        self.results = {
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "emails_synced": [],
            "emails_processed": [],
            "actions_created": []
        }
    
    def test_api_health(self):
        """Test 1: Verify API is running"""
        print("\n🔍 Test 1: API Health Check")
        print("-" * 50)
        
        try:
            # Test email actions stats endpoint
            response = requests.get(f"{self.api_base_url}/api/email-actions/stats", timeout=5)
            
            if response.status_code == 200:
                stats = response.json()
                print(f"✅ API is running")
                print(f"   Total actions: {stats.get('total_actions', 0)}")
                print(f"   Pending actions: {stats.get('pending_actions', 0)}")
                self.results["tests_passed"] += 1
                return True
            else:
                print(f"❌ API returned status {response.status_code}")
                self.results["tests_failed"] += 1
                return False
                
        except requests.exceptions.ConnectionError:
            print(f"❌ Cannot connect to API at {self.api_base_url}")
            print("   Make sure server is running: uvicorn main:app --reload")
            self.results["tests_failed"] += 1
            return False
        except Exception as e:
            print(f"❌ API health check failed: {str(e)}")
            self.results["tests_failed"] += 1
            return False
        finally:
            self.results["tests_run"] += 1
    
    def test_email_sync_api(self):
        """Test 2: Test email sync via API"""
        print("\n🔍 Test 2: Email Sync via API")
        print("-" * 50)
        
        try:
            print("📥 Calling POST /api/emails/sync...")
            response = requests.post(
                f"{self.api_base_url}/api/emails/sync",
                params={"minutes_back": 60, "limit": 10},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Sync API successful")
                print(f"   New emails: {result['new_emails']}")
                print(f"   Updated emails: {result['updated_emails']}")
                print(f"   Total fetched: {result['total_fetched']}")
                
                self.results["emails_synced"].extend([result['new_emails']])
                self.results["tests_passed"] += 1
                return True
            else:
                print(f"❌ Sync API failed with status {response.status_code}")
                print(f"   Response: {response.text}")
                self.results["tests_failed"] += 1
                return False
                
        except Exception as e:
            print(f"❌ Email sync API failed: {str(e)}")
            self.results["tests_failed"] += 1
            return False
        finally:
            self.results["tests_run"] += 1
    
    def test_list_emails_api(self):
        """Test 3: List emails via API"""
        print("\n🔍 Test 3: List Emails via API")
        print("-" * 50)
        
        try:
            print("📋 Calling GET /api/emails...")
            response = requests.get(
                f"{self.api_base_url}/api/emails",
                params={"page": 1, "page_size": 5},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                emails = result.get('items', [])
                
                print(f"✅ List API successful")
                print(f"   Total emails: {result['total_count']}")
                print(f"   Retrieved: {len(emails)} emails")
                
                if emails:
                    print("\n   Recent emails:")
                    for email in emails[:3]:
                        print(f"   - {email['subject']}")
                        print(f"     From: {email['from_email']}")
                        print(f"     Processed: {email['processed']}")
                
                self.results["tests_passed"] += 1
                return emails
            else:
                print(f"❌ List API failed with status {response.status_code}")
                self.results["tests_failed"] += 1
                return []
                
        except Exception as e:
            print(f"❌ List emails API failed: {str(e)}")
            self.results["tests_failed"] += 1
            return []
        finally:
            self.results["tests_run"] += 1
    
    def test_process_email_async(self, email_id: str):
        """Test 4: Process email through async workflow"""
        print(f"\n🔍 Test 4: Process Email Async (ID: {email_id})")
        print("-" * 50)
        
        try:
            # Call process API
            print(f"📤 Calling POST /api/emails/{email_id}/process...")
            response = requests.post(
                f"{self.api_base_url}/api/emails/{email_id}/process",
                timeout=10
            )
            
            if response.status_code != 200:
                print(f"❌ Process API failed with status {response.status_code}")
                print(f"   Response: {response.text}")
                self.results["tests_failed"] += 1
                return False
            
            result = response.json()
            print(f"✅ Process API successful")
            print(f"   Message: {result['message']}")
            print(f"   Workflow triggered: {result['workflow_triggered']}")
            
            if not result['workflow_triggered']:
                print("   ℹ️  Email already processed")
                self.results["tests_passed"] += 1
                return True
            
            # Extract task ID from message if available
            task_id = None
            if 'task:' in result['message']:
                task_id = result['message'].split('task: ')[1].split(')')[0]
                print(f"   Task ID: {task_id}")
            
            # Wait for processing
            print("\n⏳ Waiting for async processing...")
            time.sleep(5)  # Initial wait
            
            # Check task status
            if task_id:
                task_result = celery_app.AsyncResult(task_id)
                max_wait = 30
                waited = 5
                
                while waited < max_wait and task_result.state == 'PENDING':
                    print(f"   Status: {task_result.state} ({waited}s)...")
                    time.sleep(2)
                    waited += 2
                
                print(f"   Final status: {task_result.state}")
            
            # Check if email was processed
            with next(db_session()) as db:
                email = db.query(Email).filter(Email.id == email_id).first()
                if email and email.processed:
                    print(f"✅ Email marked as processed")
                    print(f"   Processing status: {email.processing_status}")
                    
                    # Check for created actions
                    actions = db.query(EmailAction).filter(
                        EmailAction.email_id == str(email_id)
                    ).all()
                    
                    if actions:
                        print(f"\n📎 Actions created: {len(actions)}")
                        for action in actions:
                            print(f"   - {action.action_type} ({action.status})")
                            print(f"     Confidence: {action.confidence_score}")
                            self.results["actions_created"].append(str(action.id))
                    else:
                        print("\n⚠️  No actions created")
                    
                    self.results["emails_processed"].append(email_id)
                    self.results["tests_passed"] += 1
                    return True
                else:
                    print("❌ Email not marked as processed")
                    self.results["tests_failed"] += 1
                    return False
                    
        except Exception as e:
            print(f"❌ Process email async failed: {str(e)}")
            import traceback
            traceback.print_exc()
            self.results["tests_failed"] += 1
            return False
        finally:
            self.results["tests_run"] += 1
    
    def test_event_processing(self):
        """Test 5: Check event processing status"""
        print("\n🔍 Test 5: Event Processing Status")
        print("-" * 50)
        
        try:
            with next(db_session()) as db:
                # Get recent EMAIL_ACTIONS events
                recent_events = db.query(Event).filter(
                    Event.workflow_type == 'EMAIL_ACTIONS'
                ).order_by(Event.created_at.desc()).limit(5).all()
                
                if not recent_events:
                    print("⚠️  No EMAIL_ACTIONS events found")
                    return
                
                print(f"📨 Found {len(recent_events)} recent EMAIL_ACTIONS events")
                
                processed = 0
                pending = 0
                
                for event in recent_events:
                    if event.task_context:
                        processed += 1
                        print(f"\n✅ Event {event.id[:8]}... - Processed")
                        if 'email_id' in event.data:
                            print(f"   Email ID: {event.data['email_id']}")
                    else:
                        pending += 1
                        print(f"\n⏳ Event {event.id[:8]}... - Pending")
                
                print(f"\n📊 Summary:")
                print(f"   Processed: {processed}")
                print(f"   Pending: {pending}")
                
                self.results["tests_passed"] += 1
                
        except Exception as e:
            print(f"❌ Event check failed: {str(e)}")
            self.results["tests_failed"] += 1
        finally:
            self.results["tests_run"] += 1
    
    def test_celery_queue_status(self):
        """Test 6: Check Celery queue status"""
        print("\n🔍 Test 6: Celery Queue Status")
        print("-" * 50)
        
        try:
            inspect = celery_app.control.inspect()
            
            # Check active tasks
            active = inspect.active()
            if active:
                total_active = sum(len(tasks) for tasks in active.values())
                print(f"📋 Active tasks: {total_active}")
                for worker, tasks in active.items():
                    if tasks:
                        print(f"   Worker {worker}: {len(tasks)} tasks")
            else:
                print("   No active tasks")
            
            # Check reserved tasks
            reserved = inspect.reserved()
            if reserved:
                total_reserved = sum(len(tasks) for tasks in reserved.values())
                print(f"📋 Reserved tasks: {total_reserved}")
            
            # Check stats
            stats = inspect.stats()
            if stats:
                for worker, info in stats.items():
                    total_tasks = info.get('total', {})
                    print(f"\n📊 Worker {worker} stats:")
                    print(f"   Total tasks: {sum(total_tasks.values())}")
                    if 'process_incoming_event' in total_tasks:
                        print(f"   process_incoming_event: {total_tasks['process_incoming_event']}")
            
            self.results["tests_passed"] += 1
            
        except Exception as e:
            print(f"❌ Celery status check failed: {str(e)}")
            self.results["tests_failed"] += 1
        finally:
            self.results["tests_run"] += 1
    
    def run_all_tests(self):
        """Run all async workflow tests"""
        print("=" * 60)
        print("🧪 ASYNC EMAIL WORKFLOW TESTS")
        print("=" * 60)
        
        # Test 1: API health
        if not self.test_api_health():
            print("\n⛔ API not running - stopping tests")
            return self.print_summary()
        
        # Test 2: Email sync
        self.test_email_sync_api()
        
        # Test 3: List emails
        emails = self.test_list_emails_api()
        
        # Test 4: Process an email
        if emails:
            # Find an unprocessed email
            unprocessed = next((e for e in emails if not e['processed']), None)
            if unprocessed:
                self.test_process_email_async(unprocessed['id'])
            else:
                # Process the most recent email anyway
                print("\n⚠️  No unprocessed emails, using most recent")
                self.test_process_email_async(emails[0]['id'])
        
        # Test 5: Check events
        self.test_event_processing()
        
        # Test 6: Celery status
        self.test_celery_queue_status()
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 ASYNC WORKFLOW TEST SUMMARY")
        print("=" * 60)
        print(f"Tests Run:         {self.results['tests_run']}")
        print(f"Tests Passed:      {self.results['tests_passed']} ✅")
        print(f"Tests Failed:      {self.results['tests_failed']} ❌")
        print(f"Emails Synced:     {sum(self.results['emails_synced'])}")
        print(f"Emails Processed:  {len(self.results['emails_processed'])}")
        print(f"Actions Created:   {len(self.results['actions_created'])}")
        
        print("\n" + "=" * 60)
        
        return self.results


def main():
    """Run async workflow tests"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test async email workflow')
    parser.add_argument('--api-url', default='http://localhost:8080',
                        help='API base URL (default: http://localhost:8080)')
    parser.add_argument('--email-id', help='Specific email ID to process')
    
    args = parser.parse_args()
    
    tester = AsyncWorkflowTester(api_base_url=args.api_url)
    
    if args.email_id:
        # Test specific email
        tester.test_api_health()
        tester.test_process_email_async(args.email_id)
        tester.test_event_processing()
    else:
        # Run all tests
        tester.run_all_tests()


if __name__ == "__main__":
    main()