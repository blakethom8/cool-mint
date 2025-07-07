# Salesforce User Sync Service

This service handles the synchronization of Salesforce users with our local PostgreSQL database.

## Overview

The User Sync Service is designed to:
- Use the REST API with pagination to efficiently sync user data
- Support flexible sync modes (full sync, recent data, custom date range)
- Implement read-only operations to ensure data safety
- Handle user data including address information
- Provide detailed progress tracking and statistics

## Components

- `user_sync_service.py`: Main service for syncing users
- `rest_user_service.py`: Read-only REST API wrapper with pagination support
- `run_user_sync.py`: CLI script to run the sync process

## Usage

### Command Line

```bash
# Full sync of all users
python run_user_sync.py --mode full

# Sync recent users (default 30 days)
python run_user_sync.py --mode recent --days 30

# Sync from a specific date
python run_user_sync.py --mode custom --start-date 2024-01-01

# Optional: limit number of records
python run_user_sync.py --mode full --limit 1000
```

### Programmatic Usage

```python
from app.services.salesforce_files.user_sync.user_sync_service import UserSyncService
from app.services.salesforce_files.user_sync.rest_user_service import RestUserService

# Initialize services
rest_service = RestUserService()
sync_service = UserSyncService(db_session, rest_service)

# Run sync with desired mode
sync_service.sync_users(modified_since=last_sync_date)
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

## Data Model

The service syncs the following user fields:
- Standard fields (Id, Username, Name, Email, etc.)
- Address information (stored as JSONB)
- Custom fields (External_ID__c)
- System fields (CreatedDate, LastModifiedDate, etc.)

All data is stored in the `sf_users` table with appropriate indexes and constraints. 