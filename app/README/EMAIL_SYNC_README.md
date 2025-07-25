# Email Sync System Documentation

This system provides flexible email synchronization with Nylas, supporting both webhook-based real-time updates and manual sync for development.

## Quick Start

### 1. Check Status
```bash
python test_email_sync_simple.py
```

### 2. Manual Sync (Development Mode)
```bash
# Sync emails from last 30 minutes
python sync_emails_simple.py

# Sync emails from last hour
python sync_emails_simple.py --minutes 60

# Check email database status
python sync_emails_simple.py --status
```

### 3. Webhook Mode (Production)
```bash
# First, ensure your FastAPI server is running on port 8080
uvicorn main:app --host 0.0.0.0 --port 8080 --reload

# In another terminal, start the webhook
python scripts/setup_email_webhook.py

# List existing webhooks
python scripts/setup_email_webhook.py --list

# Cleanup webhooks
python scripts/setup_email_webhook.py --cleanup
```

## Configuration

The system uses environment variables set in `.env`:

```env
# Email Sync Mode
EMAIL_SYNC_MODE=manual  # Options: webhook, manual, scheduled

# Sync Settings
EMAIL_SYNC_INTERVAL=5     # Minutes between syncs (for scheduled mode)
EMAIL_SYNC_LOOKBACK=30    # Minutes to look back when syncing
EMAIL_BATCH_SIZE=50       # Max emails per sync
EMAIL_PROCESS_ON_SYNC=true # Queue emails for AI processing
```

## Architecture

### Manual Mode (Development)
- Run `sync_emails_simple.py` whenever you want to fetch new emails
- Emails are fetched from the last N minutes (configurable)
- Perfect for development and testing

### Webhook Mode (Production)
- Real-time email notifications via Nylas webhooks
- Requires Pinggy tunnel to expose local server
- Automatically processes emails as they arrive

## File Structure

```
app/
├── EMAIL_SYNC_README.md           # This file
├── manage_email_sync.py           # Unified management tool
├── sync_emails_simple.py          # Simple sync script (no Celery)
├── test_email_sync_simple.py      # Test configuration
│
├── config/
│   └── email_sync_config.py      # Configuration management
│
├── services/
│   ├── nylas_email_service.py    # Core Nylas integration
│   └── email_sync_manager.py     # Sync orchestration
│
├── scripts/
│   ├── sync_emails.py            # Full sync script (with Celery)
│   └── setup_email_webhook.py    # Webhook setup tool
│
├── api/
│   └── email_webhook.py          # Webhook endpoint
│
└── database/
    └── data_models/
        └── email_data.py         # Email database models
```

## Database Schema

The system stores emails in three tables:
- `emails` - Main email data
- `email_attachments` - Attachment metadata
- `email_activities` - Actions taken on emails

## Common Tasks

### Switch Between Modes
```python
from config.email_sync_config import EmailSyncConfig

# Switch to webhook mode
EmailSyncConfig.set_sync_mode("webhook")

# Switch to manual mode
EmailSyncConfig.set_sync_mode("manual")
```

### Sync Recent Emails (Python)
```python
from services.nylas_email_service import NylasEmailService
from database.session import db_session

for session in db_session():
    service = NylasEmailService(session)
    emails = service.sync_recent_emails(grant_id, limit=20)
    break
```

### Process Unprocessed Emails
```bash
python scripts/sync_emails.py --all
```

## Troubleshooting

### Webhook Issues
1. Ensure FastAPI is running on port 8080
2. Check that Pinggy tunnel is active
3. Verify webhook secret in `.env`
4. Use `--list` to see existing webhooks

### Sync Issues
1. Verify Nylas credentials in `.env`
2. Check grant ID is valid
3. Look at sync timestamps with `--status`
4. Check for errors in sync output

### Database Issues
1. Ensure migrations are applied: `alembic upgrade head`
2. Check table existence: `python check_email_tables.py`
3. Verify database connection settings

## Next Steps

After emails are synced, you can:
1. Create email processing workflows
2. Implement AI classification
3. Set up automated actions
4. Build email analytics

For production deployment:
1. Use webhook mode with a public server
2. Implement proper error handling
3. Set up monitoring and alerts
4. Configure scheduled syncs as backup