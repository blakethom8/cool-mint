# Juno Email Assistant Debug Tools

This directory contains debugging tools for the Juno Email Assistant workflow. Since this is the first implementation using Celery for async processing, these tools help test and debug each layer of the system.

## 🐳 Docker Environment Notice

Your Celery worker runs in a Docker container, which affects how you debug:

- **Celery Worker**: Runs in `${PROJECT_NAME}_celery_worker` container
- **Redis**: Runs in `${PROJECT_NAME}_redis` container  
- **API**: Runs in `${PROJECT_NAME}_api` container
- **Database**: Runs in `supabase-db` container

### Quick Docker Debugging

Use the provided Docker debug helper:

```bash
# Make it executable
chmod +x debug/docker_debug.sh

# Check container status
./debug/docker_debug.sh check

# View Celery logs
./debug/docker_debug.sh logs

# Check Celery status
./debug/docker_debug.sh celery-status

# Run tests inside containers
./debug/docker_debug.sh test-sync
./debug/docker_debug.sh test-celery
./debug/docker_debug.sh test-async

# Database inspection
./debug/docker_debug.sh db-summary
./debug/docker_debug.sh db-emails
```

## Prerequisites

Before running these tests, ensure you have:

1. **PostgreSQL** running
2. **Redis** running (required for Celery)
3. **Environment variables** configured (.env file)
4. **Python dependencies** installed

## Required Services

### Option A: Using Docker (Recommended)

```bash
# From docker directory
cd docker/

# Start all services
./start.sh

# Check if everything is running
docker ps
```

### Option B: Running Locally

If running services outside Docker, you'll need to:

1. Update Redis connection in tests
2. Ensure database is accessible at localhost:5433
3. Set environment variables properly

```bash
# Start services manually
redis-server
celery -A worker.config worker --loglevel=info
uvicorn main:app --host 0.0.0.0 --port 8080 --reload
npm run dev  # Frontend
```

## Debug Tools Overview

### Phase 1: Synchronous Testing (`test_sync_workflow.py`)

Tests core functionality without Celery to isolate business logic issues.

```bash
# Run all synchronous tests
python debug/test_sync_workflow.py
```

**What it tests:**
- Database connection
- Email service functionality
- Direct workflow execution (no Celery)
- Nylas sync (if configured)

**Use when:** You want to verify the core logic works before adding async complexity.

### Phase 2: Celery Testing (`test_celery_basic.py`)

Tests basic Celery functionality with simple tasks.

```bash
# Run Celery tests
python debug/test_celery_basic.py
```

**What it tests:**
- Celery/Redis connection
- Simple hello world tasks
- Task with parameters
- Existing workflow task execution
- Task monitoring

**Use when:** Celery tasks aren't executing or you're not sure if Celery is configured correctly.

### Phase 3: Async Workflow Testing (`test_async_workflow.py`)

Tests the complete end-to-end async email processing.

```bash
# Run all async tests
python debug/test_async_workflow.py

# Test specific email
python debug/test_async_workflow.py --email-id <email-uuid>

# Test with different API URL
python debug/test_async_workflow.py --api-url http://localhost:3000
```

**What it tests:**
- API health check
- Email sync via API
- Async email processing
- Event creation and processing
- Celery queue status

**Use when:** Testing the full workflow through the API with Celery processing.

### Database Inspector (`db_inspector.py`)

Inspect current database state for debugging.

```bash
# Show summary of all tables
python debug/db_inspector.py summary

# Inspect emails
python debug/db_inspector.py emails
python debug/db_inspector.py emails --limit 20
python debug/db_inspector.py emails --show-all

# Inspect events (Celery queue)
python debug/db_inspector.py events

# Inspect email actions
python debug/db_inspector.py actions

# Search emails by subject
python debug/db_inspector.py emails --search "meeting"

# Show everything
python debug/db_inspector.py all
```

**Use when:** You need to see what's in the database or track down specific records.

## Common Debugging Scenarios

### 1. "Emails aren't syncing"

```bash
# First, test sync directly
python debug/test_sync_workflow.py

# Check if emails are in database
python debug/db_inspector.py emails

# Test sync via API
python debug/test_async_workflow.py
```

### 2. "Email processing isn't working"

```bash
# Test workflow directly (no Celery)
python debug/test_sync_workflow.py

# Check if Celery is working
python debug/test_celery_basic.py

# Find an email and process it
python debug/db_inspector.py emails --search "test"
python debug/test_async_workflow.py --email-id <email-id>
```

### 3. "Actions aren't being created"

```bash
# Check recent actions
python debug/db_inspector.py actions

# Check events and their processing status
python debug/db_inspector.py events

# Test workflow with known email
python debug/test_sync_workflow.py
```

### 4. "Celery tasks are stuck"

```bash
# Check Celery connection
python debug/test_celery_basic.py

# Monitor Celery queue
celery -A worker.config inspect active
celery -A worker.config inspect reserved
celery -A worker.config inspect stats

# Check event processing
python debug/db_inspector.py events
```

## Typical Testing Flow

1. **Start with Phase 1** - Verify core functionality works
2. **Move to Phase 2** - Ensure Celery is configured properly
3. **Run Phase 3** - Test the complete async workflow
4. **Use DB Inspector** - Debug specific issues

## API Testing with curl

You can also test the API directly:

```bash
# Check API health
curl http://localhost:8080/api/email-actions/stats | jq

# Sync emails
curl -X POST "http://localhost:8080/api/emails/sync?minutes_back=30&limit=10" | jq

# List emails
curl "http://localhost:8080/api/emails?page=1&page_size=5" | jq

# Process specific email
curl -X POST "http://localhost:8080/api/emails/{email-id}/process" | jq
```

## Troubleshooting

### Missing imports or modules

If you get import errors, make sure you're running from the `app` directory:

```bash
cd /path/to/cool-mint/app
python debug/test_sync_workflow.py
```

### Celery not picking up tasks

1. Check Redis is running: `redis-cli ping`
2. Check Celery worker output for errors
3. Verify CELERY_BROKER_URL in environment

### Database connection errors

1. Check PostgreSQL is running
2. Verify DATABASE_URL in environment
3. Check if migrations are up to date

### Email sync fails

1. Verify NYLAS_API_KEY and NYLAS_GRANT_ID in environment
2. Check Nylas webhook configuration
3. Test with manual sync mode first

## Next Steps

After debugging:

1. Check the Juno Assistant UI at http://localhost:3000/juno-assistant
2. Click "Emails" tab to see synced emails
3. Select emails and click "Process with Juno"
4. Switch to "Pending Actions" to review AI results
5. Approve or modify actions as needed