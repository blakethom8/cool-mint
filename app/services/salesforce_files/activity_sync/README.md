# Salesforce Activity Sync Service

This service handles the synchronization of Salesforce activities (Tasks and Events) with our local PostgreSQL database.

## Overview

The Activity Sync Service is designed to:
- Use the REST API with pagination to efficiently sync activities
- Support flexible sync modes (full sync, recent data, custom date range)
- Implement read-only operations to ensure data safety
- Handle both Tasks and Events from Salesforce
- Provide detailed progress tracking and statistics

## Components

- `activity_sync_service.py`: Main service for syncing activities
- `rest_activity_service.py`: Read-only REST API wrapper with pagination support
- `run_activity_sync.py`: CLI script to run the sync process

## Usage

### Command Line

```bash
# Full sync of all activities
python run_activity_sync.py --mode full

# Sync recent activities (default 30 days)
python run_activity_sync.py --mode recent --days 30

# Sync from a specific date
python run_activity_sync.py --mode custom --start-date 2024-01-01

# Optional: limit number of records
python run_activity_sync.py --mode full --limit 1000
```

### Programmatic Usage

```python
from app.services.salesforce_files.activity_sync.activity_sync_service import ActivitySyncService
from app.services.salesforce_files.activity_sync.rest_activity_service import RestActivityService

# Initialize services
rest_service = RestActivityService()
sync_service = ActivitySyncService(db_session, rest_service)

# Run sync with desired mode
sync_service.sync_activities(modified_since=last_sync_date)
```

## Security

This service strictly enforces read-only operations through:
1. Using a read-only REST service wrapper
2. Validating all SOQL queries
3. Monitoring API usage and limits

## Performance

- Uses pagination (200 records per batch) for efficient data retrieval
- Provides progress tracking for long-running syncs
- Optimized database operations with proper error handling
- Detailed logging and statistics for monitoring 