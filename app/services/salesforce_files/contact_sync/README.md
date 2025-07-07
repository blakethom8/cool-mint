# Salesforce Contact Sync Service

This service handles the synchronization of Salesforce contacts with our local PostgreSQL database.

## Overview

The Contact Sync Service provides two approaches for syncing contact data:
- **Bulk API**: Efficient for large datasets (600,000+ contacts)
- **REST API**: Flexible for smaller datasets and testing
- Support flexible sync modes (full sync, recent data, custom date range)
- Implement read-only operations to ensure data safety
- Handle comprehensive contact data including address and custom fields
- Provide detailed progress tracking and statistics

## Components

- `bulk_contact_sync_service.py`: Bulk API service for large-scale contact sync
- `sf_contact_sync_service.py`: REST API service for flexible contact sync
- `run_contact_sync.py`: CLI script to run the sync process

## Usage

### Command Line

```bash
# Test API connections
python run_contact_sync.py --test

# Full sync using Bulk API (recommended for large datasets)
python run_contact_sync.py --mode bulk --full

# Incremental sync using Bulk API (last 7 days)
python run_contact_sync.py --mode bulk --days 7

# Custom date range using Bulk API
python run_contact_sync.py --mode bulk --start-date 2024-01-01

# REST API sync with limit (good for testing)
python run_contact_sync.py --mode rest --limit 1000

# Incremental sync with custom batch size
python run_contact_sync.py --mode bulk --days 30 --batch-size 500
```

### Programmatic Usage

#### Bulk API Approach
```python
from app.services.salesforce_files.contact_sync.bulk_contact_sync_service import BulkContactSyncService
from app.services.salesforce_files.bulk_salesforce_service import BulkSalesforceService

# Initialize services
sf_bulk_service = BulkSalesforceService()
sync_service = BulkContactSyncService(db_session, sf_bulk_service)

# Run bulk sync
stats = sync_service.bulk_sync_contacts(modified_since=last_sync_date, batch_size=1000)
```

#### REST API Approach
```python
from app.services.salesforce_files.contact_sync.sf_contact_sync_service import SfContactSyncService
from app.services.salesforce_files.salesforce_service import ReadOnlySalesforceService

# Initialize services
sf_service = ReadOnlySalesforceService()
sync_service = SfContactSyncService(db_session, sf_service)

# Run REST sync
contacts = sync_service.sync_contacts(modified_since=last_sync_date, limit=5000)
```

## API Comparison

| Feature | Bulk API | REST API |
|---------|----------|----------|
| **Best For** | Large datasets (10K+ records) | Small datasets, testing |
| **Performance** | Very fast for bulk operations | Moderate, good for incremental |
| **Memory Usage** | Low (streaming) | Higher (loads all in memory) |
| **Error Handling** | Batch-level | Individual record level |
| **Flexibility** | Less flexible queries | More flexible, real-time |
| **API Limits** | Separate bulk limits | Uses standard API limits |

## Performance Characteristics

### Bulk API Performance
- **Large datasets**: 600,000+ contacts in ~3 hours
- **Streaming approach**: Low memory usage
- **Batch processing**: 1,000 records per database batch
- **Optimal for**: Initial full syncs, large incremental syncs

### REST API Performance
- **Small datasets**: 1,000-10,000 contacts efficiently
- **Real-time processing**: Immediate feedback per record
- **Memory usage**: Higher for large datasets
- **Optimal for**: Testing, small incremental syncs, targeted updates

## Security

This service strictly enforces read-only operations through:
1. Using read-only service wrappers for both APIs
2. Validating all SOQL queries
3. Monitoring API usage and limits
4. No write operations back to Salesforce

## Data Model

The service syncs comprehensive contact fields including:

### Standard Fields
- **Core Identity**: Id, Name, FirstName, LastName, Salutation, etc.
- **Contact Information**: Email, Phone, MobilePhone, Fax, Title
- **Mailing Address**: Street, City, State, PostalCode, Country, Coordinates
- **Activity Tracking**: LastActivityDate, LastViewedDate, LastReferencedDate

### Custom Fields
- **Identity & Classification**: External_ID__c, NPI__c, Specialty__c, Is_Physician__c
- **Provider Information**: Provider_Type__c, Provider_Participation__c
- **Minnesota Specific**: 50+ MN-specific fields for local operations
- **Business Entity**: Network associations, practice locations
- **Address Components**: Detailed MN address structure

All data is stored in the `sf_contacts` table with:
- Unique constraints on Salesforce ID
- Proper indexes for query performance
- JSONB fields for flexible data storage
- Foreign key relationships to other Salesforce entities

## Sync Modes

### 1. Full Sync (`--full`)
- Syncs all contacts from Salesforce
- Use for initial setup or complete refresh
- **Bulk API recommended** for large datasets

### 2. Incremental Sync (`--days N`)
- Syncs contacts modified in the last N days
- Default mode for regular maintenance
- Efficient for ongoing synchronization

### 3. Custom Date Range (`--start-date YYYY-MM-DD`)
- Syncs contacts modified since a specific date
- Useful for targeted data recovery or catch-up syncs

### 4. Limited Sync (`--limit N`)
- Syncs up to N contacts (REST API only)
- Perfect for testing and development

## Error Handling

### Bulk API Error Handling
- **Batch-level processing**: Failed batches are logged and retried
- **Data validation**: Comprehensive field validation before database operations
- **Transaction management**: Rollback on batch failures
- **Detailed logging**: Complete error context for troubleshooting

### REST API Error Handling
- **Individual record processing**: Failed records don't affect others
- **Graceful degradation**: Continues processing despite individual failures
- **Detailed error logs**: Per-record error information
- **Statistics tracking**: Success/failure rates

## Best Practices

### Choosing the Right API

#### Use Bulk API When:
- Syncing more than 10,000 contacts
- Performing initial full sync
- Memory efficiency is important
- Processing time is not critical

#### Use REST API When:
- Syncing fewer than 10,000 contacts
- Need real-time feedback
- Testing sync logic
- Incremental updates with immediate visibility

### Recommended Sync Patterns

#### Initial Setup
```bash
# Test connections first
python run_contact_sync.py --test

# Full sync using Bulk API
python run_contact_sync.py --mode bulk --full
```

#### Daily Maintenance
```bash
# Incremental sync (last 24 hours)
python run_contact_sync.py --mode bulk --days 1
```

#### Weekly Maintenance
```bash
# Broader incremental sync (last 7 days)
python run_contact_sync.py --mode bulk --days 7
```

#### Development/Testing
```bash
# Small test sync
python run_contact_sync.py --mode rest --limit 100
```

## Monitoring & Logging

### Log Files
- **contact_sync.log**: Detailed sync operations and statistics
- **Console output**: Real-time progress and results

### Key Metrics Tracked
- Total contacts retrieved vs processed
- New vs updated records
- Processing rates (records/second)
- Error counts and types
- Database operation statistics
- API usage and efficiency

### Statistics Output
```
Final Statistics:
Total retrieved: 125,000
Total processed: 124,850
New records: 1,200
Updated records: 123,650
Errors: 150
Processing rate: 45.2 records/second
```

## Database Operations

### UPSERT Strategy
The service uses PostgreSQL's `ON CONFLICT` functionality:
- **Updates**: All Salesforce data fields
- **Preserves**: Local database metadata (id, created_at)
- **Maintains**: Data integrity with proper constraint handling

### Batch Processing
- **Bulk API**: 1,000 records per database batch (configurable)
- **REST API**: Individual record processing
- **Memory efficient**: Streaming approach for large datasets
- **Transaction safety**: Proper rollback on errors

## Troubleshooting

### Common Issues

#### Authentication Errors
- **Cause**: Invalid credentials or expired tokens
- **Solution**: Verify environment variables and test connections
- **Command**: `python run_contact_sync.py --test`

#### Memory Issues (Large Syncs)
- **Cause**: Large datasets with REST API
- **Solution**: Use Bulk API or reduce batch sizes
- **Command**: `python run_contact_sync.py --mode bulk --batch-size 500`

#### Slow Performance
- **Cause**: Network issues or large datasets with REST API
- **Solution**: Switch to Bulk API or use incremental syncs
- **Monitoring**: Check processing rates in logs

#### Database Constraint Errors
- **Cause**: Data integrity issues or foreign key violations
- **Solution**: Check error logs for specific field issues
- **Prevention**: Regular data validation and testing

### Health Checks
```bash
# Test all connections
python run_contact_sync.py --test

# Small test sync to verify functionality
python run_contact_sync.py --mode rest --limit 10

# Check recent incremental sync
python run_contact_sync.py --mode bulk --days 1
```

## Integration Notes

### Dependencies
- Requires `bulk_salesforce_service.py` and `salesforce_service.py` from parent directory
- Uses shared database models from `app.database.data_models.salesforce_data`
- Integrates with existing session management

### Import Path Updates
When moving files, update any existing imports:
```python
# Old import
from app.services.salesforce_files.bulk_contact_sync_service import BulkContactSyncService

# New import
from app.services.salesforce_files.contact_sync.bulk_contact_sync_service import BulkContactSyncService
```

## Related Services

- **targeted_sync/**: Optimized sync for contacts with activities only
- **activity_sync/**: Syncs tasks and events
- **user_sync/**: Syncs Salesforce users
- **taskwhorelation_sync/**: Syncs task-contact relationships

This contact sync service provides the foundation for comprehensive Salesforce contact data management with both high-performance bulk operations and flexible REST-based approaches. 