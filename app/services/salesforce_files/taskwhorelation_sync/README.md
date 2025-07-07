# Salesforce TaskWhoRelation Sync Service

This service handles the synchronization of Salesforce TaskWhoRelation records with our local PostgreSQL database. TaskWhoRelation records represent the many-to-many relationship between Tasks and Contacts in Salesforce.

## Overview

The TaskWhoRelation Sync Service is designed to:
- Use the REST API with cursor-based pagination to efficiently sync relationship data
- Support flexible sync modes (full sync, recent data, custom date range)
- Implement read-only operations to ensure data safety
- Handle task-contact relationships with proper foreign key management
- Provide detailed progress tracking and comprehensive logging
- Use resilient processing that continues even when individual records fail

## Components

- `taskwhorelation_sync_service.py`: Main service for syncing TaskWhoRelation records
- `rest_taskwhorelation_service.py`: Read-only REST API wrapper with cursor-based pagination
- `run_taskwhorelation_sync.py`: CLI script to run the sync process

## Usage

### Command Line

```bash
# Full sync of all TaskWhoRelation records
python run_taskwhorelation_sync.py --mode full

# Sync recent records (default 30 days)
python run_taskwhorelation_sync.py --mode recent --days 30

# Sync from a specific date
python run_taskwhorelation_sync.py --mode custom --start-date 2024-01-01

# Optional: limit number of records for testing
python run_taskwhorelation_sync.py --mode full --limit 1000
```

### Programmatic Usage

```python
from app.services.salesforce_files.taskwhorelation_sync.taskwhorelation_sync_service import TaskWhoRelationSyncService
from app.services.salesforce_files.taskwhorelation_sync.rest_taskwhorelation_service import RestTaskWhoRelationService

# Initialize services
rest_service = RestTaskWhoRelationService()
sync_service = TaskWhoRelationSyncService(db_session, rest_service)

# Run sync with desired mode
sync_service.sync_taskwhorelations(modified_since=last_sync_date)
```

## Resilient Processing Architecture

### Individual Record Processing
- Each record is processed individually to prevent single failures from breaking entire batches
- Failed records are logged with detailed error information and continue processing
- Comprehensive statistics tracking for both successful and failed records

### Error Handling Strategy
- **Foreign Key Violations**: Common when TaskWhoRelations reference Tasks not yet in our database
- **Graceful Degradation**: Sync continues even with failed records
- **Detailed Error Logging**: Full error context captured for troubleshooting

### Batch Processing
- 200 records per batch for optimal performance
- Progress tracking with batch-level statistics
- Individual record processing within each batch

## Comprehensive Logging & Results

### Results File Structure
Each sync run generates a timestamped markdown file in `sync_results/` with:

```
sync_results/taskwhorelation_sync_results_YYYYMMDD_HHMMSS.md
```

### Results Content
- **Summary Statistics**: Total records, success rate, processing time
- **Batch-level Progress**: Success/failure counts per batch
- **Successful Records**: Complete JSON logs of all successfully synced records
- **Failed Records**: Complete JSON logs with full error details and context
- **Error Analysis**: Breakdown of error types and frequencies

### Example Results Structure
```markdown
# TaskWhoRelation Sync Results - 2025-07-06 18:22:14

## Summary
- **Total Records Retrieved**: 2,392
- **Total Successful**: 2,281 (95.36%)
- **Total Failed**: 111 (4.64%)
- **Processing Duration**: 3 minutes 2 seconds

## Successful Records
[Complete JSON logs of all successful records...]

## Failed Records
[Complete JSON logs with error details...]

## Error Summary
- Foreign Key Violations: 111 records
- Missing Task IDs: [List of specific Task IDs not found]
```

## Performance Characteristics

### Pagination Strategy
- **Cursor-based pagination** using record IDs to avoid OFFSET limitations
- Handles Salesforce's 2000 record OFFSET limit automatically
- Efficient for large datasets with consistent performance

### API Efficiency
- 200 records per API call for optimal throughput
- Automatic retry logic for transient failures
- API usage monitoring and reporting

### Database Operations
- Upsert operations with conflict resolution
- Individual record processing prevents batch failures
- Proper transaction handling with rollback on errors

## Security

This service strictly enforces read-only operations through:
1. Using a read-only REST service wrapper
2. Validating all SOQL queries
3. Monitoring API usage and limits
4. No write operations back to Salesforce

## Data Model

The service syncs the following TaskWhoRelation fields:
- **Standard Fields**: Id, IsDeleted, Type
- **Relationship Fields**: RelationId (Contact), TaskId (Task)
- **User Fields**: CreatedById, LastModifiedById
- **System Fields**: CreatedDate, LastModifiedDate, SystemModstamp

All data is stored in the `sf_taskwhorelations` table with:
- Foreign key constraints to `sf_activities` (TaskId) and `sf_contacts` (RelationId)
- Unique constraints on Salesforce ID
- Proper indexes for query performance

## Dependencies

### Required Tables
- `sf_activities`: Must contain Task records before syncing TaskWhoRelations
- `sf_contacts`: Must contain Contact records referenced by RelationId
- `sf_users`: Must contain User records referenced by CreatedById/LastModifiedById

### Sync Order
1. **Users** → `sf_users`
2. **Contacts** → `sf_contacts`  
3. **Activities/Tasks** → `sf_activities`
4. **TaskWhoRelations** → `sf_taskwhorelations` ← *This service*

## Troubleshooting

### Common Issues

**Foreign Key Violations**
- **Cause**: TaskWhoRelations reference Tasks not in our database
- **Solution**: Run activity sync first, or analyze failed records for missing Task IDs
- **Detection**: Check results file for specific missing Task IDs

**High Failure Rate**
- **Cause**: Missing prerequisite data (Tasks, Contacts, Users)
- **Solution**: Ensure all dependent syncs are completed first
- **Monitoring**: Results file provides detailed breakdown of error types

### Monitoring Success
- **Success Rate**: Aim for >95% success rate
- **Failed Records**: Review results file for patterns in failures
- **API Usage**: Monitor API call efficiency and limits 