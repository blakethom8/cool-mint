#!/usr/bin/env python3
"""
Test Celery Email Processing

This script demonstrates how to test async email processing with Celery.
It shows both sync and async approaches for comparison.
"""

import os
import sys
import time
from datetime import datetime
from uuid import uuid4

# Add the app directory to Python path
app_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, app_dir)

from dotenv import load_dotenv
load_dotenv()

from database.session import db_session
from database.event import Event
from database.data_models.email_data import Email
from worker.tasks import process_email_webhook


def create_test_webhook_event():
    """Create a test webhook event in the database"""
    # Simulate a Nylas webhook payload
    webhook_data = {
        "trigger": "message.created",
        "grant_id": os.environ.get("NYLAS_GRANT_ID"),
        "object_data": {
            "id": "test_" + str(uuid4())[:8],  # Fake Nylas ID
            "thread_id": "test_thread_123",
            "subject": f"Test Email - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "from": [{"email": "test@example.com", "name": "Test Sender"}],
            "to": [{"email": "thomsonblakecrm@gmail.com"}],
            "date": int(datetime.utcnow().timestamp()),
            "snippet": "This is a test email for Celery processing...",
            "body": "<html><body>This is a test email for Celery processing.</body></html>",
            "unread": True,
            "starred": False
        }
    }
    
    for session in db_session():
        # Create event
        event = Event(
            workflow_type="email_webhook",
            data=webhook_data
        )
        session.add(event)
        session.commit()
        session.refresh(event)
        
        print(f"Created test webhook event: {event.id}")
        return str(event.id)


def test_sync_processing(event_id):
    """Test synchronous processing (blocking)"""
    print("\n=== Testing SYNCHRONOUS Processing ===")
    print("This will block until complete...")
    
    start_time = time.time()
    
    # Call the task directly (synchronously)
    try:
        process_email_webhook(event_id)
        
        elapsed = time.time() - start_time
        print(f"✓ Sync processing completed in {elapsed:.2f} seconds")
        
        # Check results
        for session in db_session():
            event = session.query(Event).filter_by(id=event_id).first()
            if event and event.task_context:
                print(f"Task context: {event.task_context}")
                
                # Check if email was created
                if event.task_context.get("db_email_id"):
                    email = session.query(Email).filter_by(
                        id=event.task_context["db_email_id"]
                    ).first()
                    if email:
                        print(f"✓ Email created: {email.subject}")
            break
            
    except Exception as e:
        print(f"✗ Error in sync processing: {e}")


def test_async_processing(event_id):
    """Test asynchronous processing (non-blocking)"""
    print("\n=== Testing ASYNCHRONOUS Processing ===")
    print("This will return immediately...")
    
    start_time = time.time()
    
    try:
        # Queue the task asynchronously
        result = process_email_webhook.delay(event_id)
        
        queue_time = time.time() - start_time
        print(f"✓ Task queued in {queue_time:.4f} seconds")
        print(f"Task ID: {result.id}")
        
        # Check task status
        print("\nChecking task status...")
        for i in range(10):  # Check for up to 10 seconds
            if result.ready():
                print(f"✓ Task completed after {i+1} seconds")
                print(f"Result: {result.result}")
                break
            else:
                print(f"  Status after {i+1}s: Processing...")
                time.sleep(1)
        else:
            print("⚠ Task still processing after 10 seconds")
            
        # Check database for results
        time.sleep(1)  # Give it a moment to commit
        for session in db_session():
            event = session.query(Event).filter_by(id=event_id).first()
            if event and event.task_context:
                print(f"\nTask context: {event.task_context}")
            break
            
    except Exception as e:
        print(f"✗ Error in async processing: {e}")
        print("Is Celery worker running? Check with: docker ps | grep celery")


def test_bulk_async_processing():
    """Test processing multiple emails asynchronously"""
    print("\n=== Testing BULK ASYNC Processing ===")
    print("Creating and queueing 5 test emails...")
    
    task_results = []
    
    # Create and queue multiple tasks
    for i in range(5):
        event_id = create_test_webhook_event()
        result = process_email_webhook.delay(event_id)
        task_results.append({
            "index": i + 1,
            "event_id": event_id,
            "result": result,
            "queued_at": time.time()
        })
        print(f"  Queued task {i+1}: {result.id}")
    
    print("\nMonitoring task completion...")
    
    # Monitor completion
    all_complete = False
    start_monitor = time.time()
    
    while not all_complete and (time.time() - start_monitor) < 30:
        completed = sum(1 for t in task_results if t["result"].ready())
        print(f"  Completed: {completed}/5 tasks")
        
        if completed == len(task_results):
            all_complete = True
        else:
            time.sleep(2)
    
    # Show results
    print("\nResults:")
    for task in task_results:
        status = "✓ Complete" if task["result"].ready() else "⚠ Pending"
        elapsed = time.time() - task["queued_at"]
        print(f"  Task {task['index']}: {status} (elapsed: {elapsed:.2f}s)")


def check_celery_status():
    """Check if Celery is properly configured"""
    print("\n=== Checking Celery Configuration ===")
    
    try:
        from worker.config import celery_app
        
        # Check broker connection
        print("Checking Redis connection...")
        inspector = celery_app.control.inspect()
        stats = inspector.stats()
        
        if stats:
            print("✓ Celery workers found:")
            for worker_name, worker_stats in stats.items():
                print(f"  - {worker_name}")
        else:
            print("✗ No Celery workers found!")
            print("  Start worker with: docker-compose up celery_worker")
            
    except Exception as e:
        print(f"✗ Error checking Celery: {e}")


def main():
    """Run all tests"""
    print("Email Celery Processing Test Suite")
    print("=" * 70)
    
    # Check Celery status first
    check_celery_status()
    
    # Create test event
    print("\nCreating test webhook event...")
    event_id = create_test_webhook_event()
    
    # Test sync processing
    test_sync_processing(event_id)
    
    # Create another event for async test
    event_id2 = create_test_webhook_event()
    
    # Test async processing
    test_async_processing(event_id2)
    
    # Test bulk processing
    response = input("\nTest bulk async processing? (y/n): ")
    if response.lower() == 'y':
        test_bulk_async_processing()
    
    print("\n" + "=" * 70)
    print("Testing complete!")
    print("\nTo monitor Celery in real-time:")
    print("  docker logs -f ${PROJECT_NAME}_celery_worker")


if __name__ == "__main__":
    main()