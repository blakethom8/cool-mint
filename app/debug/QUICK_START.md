# Juno Email Assistant - Quick Start Debugging Guide

## 🚀 Quick Test Commands

### 1. First Time Setup Check
```bash
# From app directory
cd /Users/blakethomson/Documents/Repo/cool-mint/app

# Test 1: Check if core logic works (no Celery needed)
python debug/test_sync_workflow.py

# Test 2: Check if Celery is working
python debug/test_celery_basic.py

# Test 3: Check database state
python debug/db_inspector.py summary
```

### 2. If Everything is Running
```bash
# Test the complete workflow
python debug/test_async_workflow.py
```

## 🔍 Common Issues & Solutions

### "No module named 'nylas'"
**Solution:** The Nylas module is only needed for syncing. The workflow will still test other components.

### "Cannot connect to Redis"
**Solution:** Start Redis first:
```bash
redis-server
```

### "No Celery workers found"
**Solution:** Start Celery worker:
```bash
celery -A worker.config worker --loglevel=info
```

### "Cannot connect to API"
**Solution:** Start the FastAPI server:
```bash
uvicorn main:app --host 0.0.0.0 --port 8080 --reload
```

## 📝 Test Order

1. **Database Check** → `db_inspector.py summary`
2. **Core Logic** → `test_sync_workflow.py`
3. **Celery** → `test_celery_basic.py`  
4. **Full Workflow** → `test_async_workflow.py`

## 🎯 What to Look For

✅ **Good Signs:**
- Database connection successful
- Workflow executes without Celery
- Celery hello world task completes
- Email processing creates actions

❌ **Problem Signs:**
- Import errors (missing dependencies)
- Connection refused (services not running)
- Tasks stuck in PENDING
- No actions created after processing

## 💡 Quick Fixes

**Reset and try again:**
```bash
# Clear any stuck tasks
celery -A worker.config purge

# Restart services
# Ctrl+C to stop, then restart:
celery -A worker.config worker --loglevel=info
uvicorn main:app --reload
```

**Process a specific email:**
```bash
# Find an email
python debug/db_inspector.py emails --limit 5

# Process it
python debug/test_async_workflow.py --email-id <email-id-from-above>
```