# Nylas Email Integration

This directory contains all components for the Nylas email integration system.

## Directory Structure

```
nylas_email/
├── README.md                    # This file
├── __init__.py                  # Package initialization
│
├── config/                      # Configuration management
│   ├── __init__.py
│   └── email_sync_config.py     # Sync mode configuration
│
├── scripts/                     # Executable scripts
│   ├── __init__.py
│   ├── manage_email_sync.py     # Main management CLI
│   ├── sync_emails_simple.py    # Simple sync (no Celery)
│   ├── sync_emails.py           # Full sync (with Celery)
│   ├── setup_email_webhook.py   # Webhook setup with Pinggy
│   └── setup_nylas_webhook_old.py # Legacy webhook setup
│
├── tests/                       # Test scripts
│   ├── __init__.py
│   ├── test_email_sync_simple.py    # Config tests
│   ├── test_email_sync.py           # Full sync tests
│   ├── test_nylas_connection.py     # Connection tests
│   ├── check_email_tables.py        # Database verification
│   ├── check_alembic_status.py      # Migration checks
│   └── fix_alembic_version.py       # Migration fixes
│
└── (in parent services/)
    ├── nylas_email_service.py   # Core Nylas service
    └── email_sync_manager.py    # Sync orchestration
```

## Quick Start

### From the app directory:

```bash
# Test connection
python -m services.nylas_email.tests.test_nylas_connection

# Check sync status
python -m services.nylas_email.scripts.sync_emails_simple --status

# Run manual sync
python -m services.nylas_email.scripts.sync_emails_simple

# Start webhook mode
python -m services.nylas_email.scripts.setup_email_webhook
```

### Configuration

The system uses environment variables in `.env`:
- `EMAIL_SYNC_MODE`: manual, webhook, or scheduled
- `EMAIL_SYNC_LOOKBACK`: Minutes to look back when syncing
- `EMAIL_BATCH_SIZE`: Maximum emails per sync
- `EMAIL_PROCESS_ON_SYNC`: Queue for AI processing (true/false)

### Related Files

- API endpoint: `/app/api/email_webhook.py`
- Database models: `/app/database/data_models/email_data.py`
- Configuration files: `/app/config/config_auth.py`, `/app/config/config_webhook.py`

## Usage Modes

### 1. Manual Mode (Development)
Best for development and testing. Run sync on-demand:
```bash
python -m services.nylas_email.scripts.sync_emails_simple
```

### 2. Webhook Mode (Production)
Real-time email updates via webhooks:
```bash
# Start FastAPI server first
uvicorn main:app --host 0.0.0.0 --port 8080 --reload

# Then start webhook
python -m services.nylas_email.scripts.setup_email_webhook
```

### 3. Scheduled Mode (Future)
Periodic sync via cron or Celery beat (not yet implemented).

## Testing

```bash
# Test configuration
python -m services.nylas_email.tests.test_email_sync_simple

# Check database tables
python -m services.nylas_email.tests.check_email_tables

# Test full sync with processing
python -m services.nylas_email.tests.test_email_sync
```