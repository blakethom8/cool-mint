#!/usr/bin/env python3
"""
Phase 2: Basic Celery Functionality Test
Tests if Celery is configured and working with simple tasks
"""
import os
import sys
import time
from datetime import datetime

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from worker.config import celery_app
from worker.tasks import process_incoming_event
from database.event import Event
from database.repository import GenericRepository
from database.session import db_session
from workflows.workflow_registry import WorkflowRegistry


# Create a simple test task
@celery_app.task(name="test_hello_world")
def hello_world_task(name: str = "World"):
    """Simple test task to verify Celery is working"""
    message = f"Hello {name}! Task executed at {datetime.now()}"
    print(message)
    return {"status": "success", "message": message}


@celery_app.task(name="test_add_numbers")
def add_numbers_task(x: int, y: int):
    """Test task with parameters"""
    result = x + y
    return {"x": x, "y": y, "result": result, "timestamp": str(datetime.now())}


class CeleryTester:
    """Test Celery functionality"""
    
    def __init__(self):
        self.results = {
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "task_ids": []
        }
    
    def test_celery_connection(self):
        """Test 1: Verify Celery/Redis connection"""
        print("\n🔍 Test 1: Celery Connection")
        print("-" * 50)
        
        try:
            # Try to inspect active workers
            inspect = celery_app.control.inspect()
            stats = inspect.stats()
            
            if stats:
                print("✅ Celery workers found:")
                for worker, info in stats.items():
                    print(f"   - Worker: {worker}")
                    print(f"     Pool: {info.get('pool', {}).get('implementation', 'Unknown')}")
                self.results["tests_passed"] += 1
                return True
            else:
                print("❌ No Celery workers found!")
                print("   Make sure to run: celery -A worker.config worker --loglevel=info")
                self.results["tests_failed"] += 1
                return False
                
        except Exception as e:
            print(f"❌ Celery connection failed: {str(e)}")
            print("   Make sure Redis is running and Celery worker is started")
            self.results["tests_failed"] += 1
            return False
        finally:
            self.results["tests_run"] += 1
    
    def test_simple_task(self):
        """Test 2: Execute simple hello world task"""
        print("\n🔍 Test 2: Simple Hello World Task")
        print("-" * 50)
        
        try:
            # Send task
            print("📤 Sending hello_world task...")
            result = hello_world_task.delay("Juno")
            self.results["task_ids"].append(result.id)
            
            print(f"   Task ID: {result.id}")
            print("   Waiting for result...")
            
            # Wait for result (max 10 seconds)
            task_result = result.get(timeout=10)
            
            print(f"✅ Task completed successfully!")
            print(f"   Result: {task_result}")
            
            self.results["tests_passed"] += 1
            return True
            
        except Exception as e:
            print(f"❌ Task execution failed: {str(e)}")
            self.results["tests_failed"] += 1
            return False
        finally:
            self.results["tests_run"] += 1
    
    def test_task_with_params(self):
        """Test 3: Execute task with parameters"""
        print("\n🔍 Test 3: Task with Parameters")
        print("-" * 50)
        
        try:
            # Send task
            print("📤 Sending add_numbers task (5 + 3)...")
            result = add_numbers_task.delay(5, 3)
            self.results["task_ids"].append(result.id)
            
            print(f"   Task ID: {result.id}")
            print("   Waiting for result...")
            
            # Wait for result
            task_result = result.get(timeout=10)
            
            print(f"✅ Task completed successfully!")
            print(f"   Result: {task_result}")
            
            if task_result.get('result') == 8:
                print("   ✓ Calculation correct!")
                self.results["tests_passed"] += 1
                return True
            else:
                print("   ✗ Calculation incorrect!")
                self.results["tests_failed"] += 1
                return False
                
        except Exception as e:
            print(f"❌ Task execution failed: {str(e)}")
            self.results["tests_failed"] += 1
            return False
        finally:
            self.results["tests_run"] += 1
    
    def test_existing_workflow_task(self):
        """Test 4: Test process_incoming_event task with dummy data"""
        print("\n🔍 Test 4: Process Incoming Event Task")
        print("-" * 50)
        
        try:
            with next(db_session()) as db:
                # Create a test event
                print("📝 Creating test event...")
                repository = GenericRepository(session=db, model=Event)
                
                test_data = {
                    "email_id": "test-email-123",
                    "content": "Please schedule a meeting with John tomorrow at 3pm",
                    "subject": "Meeting Request",
                    "from_email": "test@example.com",
                    "is_forwarded": False,
                    "user_instruction": None
                }
                
                event = Event(
                    data=test_data,
                    workflow_type=WorkflowRegistry.EMAIL_ACTIONS.name
                )
                repository.create(obj=event)
                
                print(f"   Event created with ID: {event.id}")
                
                # Send task
                print("📤 Sending process_incoming_event task...")
                result = celery_app.send_task(
                    "process_incoming_event",
                    args=[str(event.id)]
                )
                self.results["task_ids"].append(result.id)
                
                print(f"   Task ID: {result.id}")
                print("   Waiting for result (max 30 seconds)...")
                
                # Wait for result
                task_result = result.get(timeout=30)
                
                # Check if event was updated
                db.refresh(event)
                if event.task_context:
                    print(f"✅ Task completed successfully!")
                    print(f"   Task context updated: {event.task_context}")
                    self.results["tests_passed"] += 1
                    return True
                else:
                    print("❌ Task completed but no context updated")
                    self.results["tests_failed"] += 1
                    return False
                    
        except Exception as e:
            print(f"❌ Workflow task failed: {str(e)}")
            import traceback
            traceback.print_exc()
            self.results["tests_failed"] += 1
            return False
        finally:
            self.results["tests_run"] += 1
    
    def test_task_monitoring(self):
        """Test 5: Monitor task status"""
        print("\n🔍 Test 5: Task Monitoring")
        print("-" * 50)
        
        try:
            inspect = celery_app.control.inspect()
            
            # Check active tasks
            active = inspect.active()
            if active:
                print("📋 Active tasks:")
                for worker, tasks in active.items():
                    print(f"   Worker: {worker}")
                    for task in tasks:
                        print(f"   - {task['name']} (ID: {task['id']})")
            else:
                print("   No active tasks")
            
            # Check scheduled tasks
            scheduled = inspect.scheduled()
            if scheduled:
                print("\n📅 Scheduled tasks:")
                for worker, tasks in scheduled.items():
                    print(f"   Worker: {worker}")
                    for task in tasks:
                        print(f"   - {task['request']['name']}")
            
            # Check task results for our test tasks
            if self.results["task_ids"]:
                print(f"\n📊 Test task results ({len(self.results['task_ids'])} tasks):")
                for task_id in self.results["task_ids"]:
                    result = celery_app.AsyncResult(task_id)
                    print(f"   - {task_id}: {result.state}")
            
            self.results["tests_passed"] += 1
            return True
            
        except Exception as e:
            print(f"❌ Task monitoring failed: {str(e)}")
            self.results["tests_failed"] += 1
            return False
        finally:
            self.results["tests_run"] += 1
    
    def run_all_tests(self):
        """Run all Celery tests"""
        print("=" * 60)
        print("🧪 CELERY FUNCTIONALITY TESTS")
        print("=" * 60)
        
        # Test 1: Connection
        if not self.test_celery_connection():
            print("\n⛔ Celery not connected - stopping tests")
            print("   Please ensure:")
            print("   1. Redis is running")
            print("   2. Celery worker is started:")
            print("      celery -A worker.config worker --loglevel=info")
            return self.print_summary()
        
        # Test 2: Simple task
        self.test_simple_task()
        
        # Test 3: Task with params
        self.test_task_with_params()
        
        # Test 4: Workflow task
        self.test_existing_workflow_task()
        
        # Test 5: Monitoring
        self.test_task_monitoring()
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 CELERY TEST SUMMARY")
        print("=" * 60)
        print(f"Tests Run:    {self.results['tests_run']}")
        print(f"Tests Passed: {self.results['tests_passed']} ✅")
        print(f"Tests Failed: {self.results['tests_failed']} ❌")
        print(f"Tasks Created: {len(self.results['task_ids'])}")
        
        print("\n" + "=" * 60)
        
        return self.results


def main():
    """Run Celery tests"""
    tester = CeleryTester()
    tester.run_all_tests()


if __name__ == "__main__":
    main()