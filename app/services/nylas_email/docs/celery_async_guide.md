# Celery Async Processing Guide for Email System

## Overview
Celery is a distributed task queue that allows you to run time-consuming operations asynchronously. In your infrastructure, it's used to process emails without blocking the main application.

## Architecture Components

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   FastAPI   │────▶│    Redis    │────▶│   Celery    │────▶│ PostgreSQL  │
│   Webhook   │     │   (Queue)   │     │   Worker    │     │  Database   │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

### 1. **Redis (Message Broker)**
- Acts as the queue for tasks
- Stores task messages until workers pick them up
- Running in Docker as `${PROJECT_NAME}_redis`

### 2. **Celery Worker**
- Separate process that consumes tasks from Redis
- Runs in its own Docker container
- Can scale horizontally (multiple workers)

### 3. **Task Producer (FastAPI)**
- Your main app that creates tasks
- Sends tasks to Redis queue
- Continues immediately without waiting

## How It Works

### Step 1: Task Creation (Synchronous)
When an email webhook arrives:

```python
# In api/email_webhook.py
@router.post("/nylas")
async def handle_nylas_webhook(request: Request):
    # 1. Receive webhook
    # 2. Basic validation
    # 3. Store event in database
    event = Event(data=webhook_data)
    session.add(event)
    session.commit()
    
    # 4. Queue async task
    process_email_webhook.delay(str(event.id))  # This returns immediately!
    
    # 5. Return 200 OK to Nylas
    return {"status": "queued"}
```

### Step 2: Task Queuing (Redis)
The `.delay()` method:
1. Serializes the task and arguments to JSON
2. Sends to Redis queue
3. Returns a task ID immediately
4. FastAPI continues without waiting

### Step 3: Task Execution (Asynchronous)
The Celery worker:
1. Polls Redis for new tasks
2. Deserializes the task data
3. Executes `process_email_webhook(event_id)`
4. Stores results back in Redis

## Current Email Processing Task

```python
@celery_app.task(name="process_email_webhook")
def process_email_webhook(event_id: str):
    # Runs in separate worker process
    with contextmanager(db_session)() as session:
        # 1. Get event from database
        event = repository.get(id=event_id)
        
        # 2. Process email
        email_service = NylasEmailService(session)
        email = email_service.sync_email_from_webhook(event.data)
        
        # 3. Update event with results
        event.task_context = {"status": "processed"}
        repository.update(obj=event)
```

## Benefits of Async Processing

### 1. **Non-Blocking Webhooks**
- Nylas expects quick 200 OK response
- Processing email might take seconds
- Async allows immediate response

### 2. **Reliability**
- If processing fails, task stays in queue
- Can retry failed tasks automatically
- Survives app restarts

### 3. **Scalability**
- Add more workers for higher throughput
- Process multiple emails in parallel
- Handle traffic spikes

### 4. **Monitoring**
- Track task status and results
- See queue depth and processing time
- Debug failed tasks

## Testing Async Commands

### 1. **Check if Celery is Running**
```bash
# From docker directory
docker ps | grep celery

# View Celery logs
docker logs ${PROJECT_NAME}_celery_worker
```

### 2. **Monitor Redis Queue**
```bash
# Connect to Redis
docker exec -it ${PROJECT_NAME}_redis redis-cli

# See all keys
KEYS *

# Check queue length
LLEN celery
```

### 3. **Test Simple Task**
Create a test task:

```python
# app/worker/test_tasks.py
from worker.config import celery_app
import time

@celery_app.task(name="test_task")
def test_task(message: str):
    print(f"Starting task: {message}")
    time.sleep(5)  # Simulate work
    print(f"Completed task: {message}")
    return {"status": "completed", "message": message}
```

Run from Python shell:
```python
from worker.test_tasks import test_task

# Synchronous (blocks)
result = test_task("Hello")

# Asynchronous (non-blocking)
async_result = test_task.delay("Hello Async")
print(f"Task ID: {async_result.id}")

# Check status
print(async_result.ready())  # False initially
print(async_result.result)   # None until complete
```

### 4. **Email Processing Test**
```python
# Manually trigger email processing
from worker.tasks import process_email_webhook
from database.event import Event

# Create test event
event = Event(
    workflow_type="email_webhook",
    data={
        "trigger": "message.created",
        "grant_id": "your-grant-id",
        "object_data": {"id": "test-email-id"}
    }
)
session.add(event)
session.commit()

# Queue for processing
process_email_webhook.delay(str(event.id))
```

## Celery Configuration

Your current setup (`worker/config.py`):
```python
celery_app = Celery("tasks")
celery_app.config_from_object({
    "broker_url": "redis://redis:6379/0",
    "result_backend": "redis://redis:6379/0",
    "task_serializer": "json",
    "accept_content": ["json"],
    "result_serializer": "json",
    "enable_utc": True,
})
```

Key settings:
- **broker_url**: Where to find Redis
- **result_backend**: Where to store results
- **serializer**: JSON for compatibility
- **autodiscover**: Finds tasks automatically

## Advanced Patterns

### 1. **Task Chaining**
```python
# Process email → Classify → Take action
chain = process_email.s(email_id) | classify_email.s() | take_action.s()
chain.delay()
```

### 2. **Retry Logic**
```python
@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60  # seconds
)
def process_email_with_retry(self, email_id):
    try:
        # Process email
        pass
    except Exception as exc:
        # Retry in 60 seconds
        raise self.retry(exc=exc)
```

### 3. **Scheduled Tasks**
```python
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    'sync-emails-every-10-minutes': {
        'task': 'sync_recent_emails',
        'schedule': crontab(minute='*/10'),
    },
}
```

## Monitoring and Debugging

### 1. **Flower (Web UI)**
```bash
# Install
pip install flower

# Run
celery -A worker.config flower

# Access at http://localhost:5555
```

### 2. **Command Line**
```bash
# List active tasks
celery -A worker.config inspect active

# List scheduled tasks
celery -A worker.config inspect scheduled

# Purge all tasks
celery -A worker.config purge
```

## Integration with Email System

### Current Flow:
1. Email arrives at Nylas
2. Webhook hits FastAPI endpoint
3. Endpoint queues Celery task
4. Worker processes email asynchronously
5. Email saved to database
6. Ready for AI processing

### Next Steps:
1. Add email classification task
2. Create action tasks (reply, forward, etc.)
3. Build task chains for workflows
4. Add monitoring and alerts

## Development vs Production

### Development (Manual Sync):
- Run sync scripts directly
- See output immediately
- Good for debugging

### Production (Celery):
- Automatic processing
- Scales with load
- Handles failures gracefully

Both approaches use the same `NylasEmailService`, just different execution contexts!