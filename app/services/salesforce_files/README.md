# Salesforce Services Overview

This directory contains all services for integrating with Salesforce, including data synchronization, schema exploration, and monitoring capabilities.

## Architecture Overview

The Salesforce services are built on a layered architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                    Sync Services Layer                      │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌────────┐ │
│  │ Contact     │ │ Activity    │ │ User        │ │ Task   │ │
│  │ Sync        │ │ Sync        │ │ Sync        │ │ Who    │ │
│  │             │ │             │ │             │ │ Sync   │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └────────┘ │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│                 Base Services Layer                         │
│  ┌─────────────────────┐ ┌─────────────────────────────────┐ │
│  │ salesforce_service  │ │ bulk_salesforce_service         │ │
│  │ (REST API)          │ │ (Bulk API 2.0)                 │ │
│  └─────────────────────┘ └─────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│                PostgreSQL Data Models                       │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌────────┐ │
│  │ SfContact   │ │ SfActivity  │ │ SfUser      │ │ SfTask │ │
│  │             │ │             │ │             │ │ Who    │ │
│  │             │ │             │ │             │ │ Rel    │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
salesforce_files/
├── 📁 contact_sync/           # Contact synchronization services
├── 📁 activity_sync/          # Activity (Task/Event) synchronization
├── 📁 user_sync/              # User synchronization services
├── 📁 taskwhorelation_sync/   # TaskWhoRelation synchronization
├── 📁 targeted_sync/          # Targeted contact sync (contacts with activities)
├── 📁 schema_docs/            # Schema documentation and exploration tools
├── 📁 logs/                   # Service logs and monitoring data
├── 📁 deleted/                # Deprecated/superseded files
├── 📁 New Files/              # New development files
├── 📄 salesforce_service.py   # Shared REST API service
├── 📄 bulk_salesforce_service.py  # Shared Bulk API service
├── 📄 salesforce_monitoring.py    # Monitoring and logging utilities
└── 📄 storage_calculator.py       # Storage analysis utilities
```

## Base Services

### 1. `salesforce_service.py` - REST API Service
**Purpose**: Provides read-only access to Salesforce via REST API  
**Class**: `ReadOnlySalesforceService`  
**Best For**: 
- Small to medium datasets (< 50K records)
- Complex queries with relationships
- Real-time data access
- Testing and development

**Key Features**:
- OAuth 2.0 authentication
- SOQL query execution
- Object metadata retrieval
- Relationship traversal
- Error handling and retry logic

**Used By**: All REST-based sync services (activity_sync, user_sync, taskwhorelation_sync)

### 2. `bulk_salesforce_service.py` - Bulk API Service
**Purpose**: Handles large-scale data extraction using Salesforce Bulk API 2.0  
**Class**: `BulkSalesforceService`  
**Best For**:
- Large datasets (100K+ records)
- Full data synchronization
- Batch processing operations
- Production data migrations

**Key Features**:
- Bulk API 2.0 job management
- Asynchronous processing
- CSV data parsing
- Progress monitoring
- Rate limit handling

**Used By**: Bulk-based sync services (contact_sync, targeted_sync)

### 3. `salesforce_monitoring.py` - Monitoring Service
**Purpose**: Centralized logging and monitoring for all Salesforce operations  
**Class**: `SalesforceMonitoring`  
**Features**:
- API call logging
- Performance metrics
- Error tracking
- Usage analytics

## Sync Services

### 1. Contact Sync (`contact_sync/`)
**Purpose**: Synchronizes Salesforce contacts with local `SfContact` table

**Components**:
- `bulk_contact_sync_service.py` - Bulk API implementation for large-scale sync
- `sf_contact_sync_service.py` - REST API implementation for flexible sync
- `run_contact_sync.py` - CLI interface supporting both approaches
- `README.md` - Comprehensive documentation and usage examples

**Sync Modes**:
- Full sync (all contacts)
- Incremental sync (recent changes)
- Custom date range sync
- Test mode (connection validation)

**Performance**: Handles 600K+ contacts efficiently using bulk operations

### 2. Activity Sync (`activity_sync/`)
**Purpose**: Synchronizes Salesforce Tasks and Events with local `SfActivity` table

**Components**:
- `activity_sync_service.py` - Main sync service
- `rest_activity_service.py` - REST API wrapper
- `run_activity_sync.py` - CLI interface

**Features**:
- Unified handling of Tasks and Events
- Contact relationship linking
- Activity type classification
- Batch processing with progress tracking

### 3. User Sync (`user_sync/`)
**Purpose**: Synchronizes Salesforce Users with local `SfUser` table

**Components**:
- `user_sync_service.py` - Main sync service
- `rest_user_service.py` - REST API wrapper
- `run_user_sync.py` - CLI interface

**Features**:
- User profile synchronization
- Address data handling (stored as JSON)
- Incremental sync support

### 4. TaskWhoRelation Sync (`taskwhorelation_sync/`)
**Purpose**: Synchronizes Task-Contact relationships with local `SfTaskWhoRelation` table

**Components**:
- `taskwhorelation_sync_service.py` - Main sync service
- `rest_taskwhorelation_service.py` - REST API wrapper
- `run_taskwhorelation_sync.py` - CLI interface

**Features**:
- Many-to-many relationship handling
- Foreign key constraint management
- Batch processing with detailed logging

### 5. Targeted Sync (`targeted_sync/`)
**Purpose**: Efficiently syncs only contacts that have activities logged against them

**Components**:
- `targeted_contact_sync_service.py` - Hybrid sync service
- `rest_salesforce_service.py` - REST API service
- `run_targeted_sync.sh` - Shell script interface

**Strategy**: 
1. Use REST API to identify contacts with activities
2. Use Bulk API to fetch contact data for identified contacts
3. Dramatically reduces sync time by focusing on active contacts only

## Schema Services and PostgreSQL Integration

### Schema Exploration (`schema_docs/`)
The schema documentation system bridges Salesforce metadata with PostgreSQL table definitions.

**Components**:
- `explore_schemas.py` - Schema exploration utility
- `contact_schema_datamodel.md` - Contact field documentation
- `user_schema_datamodel.md` - User field documentation
- `task_schema_datamodel.md` - Task field documentation
- `taskwhorelation_datamodel.md` - TaskWhoRelation field documentation

### Schema-to-Database Mapping Process

1. **Schema Discovery**:
   ```python
   # explore_schemas.py uses salesforce_service to discover field metadata
   metadata = self.sf_service.describe_object("Contact")
   fields = metadata["fields"]
   ```

2. **Field Categorization**:
   - Standard fields (built-in Salesforce fields)
   - Custom fields (organization-specific fields)
   - Relationship fields (references to other objects)
   - System fields (CreatedDate, LastModifiedDate, etc.)

3. **PostgreSQL Table Creation**:
   The discovered schema information is used to create SQLAlchemy models in `app/database/data_models/salesforce_data.py`:

   ```python
   class SfContact(Base):
       __tablename__ = "sf_contacts"
       
       # Standard Fields mapped from Salesforce
       salesforce_id = Column(String(18), unique=True, nullable=False)
       last_name = Column(String(80), nullable=False)  # From LastName
       first_name = Column(String(40))                 # From FirstName
       email = Column(String(80))                      # From Email
       
       # Custom Fields mapped from Salesforce
       npi = Column(String(20))                        # From NPI__c
       specialty = Column(String(255))                 # From Specialty__c
       is_physician = Column(Boolean, default=False)   # From Is_Physician__c
       
       # System Fields
       sf_created_date = Column(DateTime)              # From CreatedDate
       sf_last_modified_date = Column(DateTime)        # From LastModifiedDate
   ```

4. **Data Type Mapping**:
   - Salesforce `string` → PostgreSQL `String(length)`
   - Salesforce `boolean` → PostgreSQL `Boolean`
   - Salesforce `datetime` → PostgreSQL `DateTime`
   - Salesforce `reference` → PostgreSQL `String(18)` (Salesforce ID)
   - Salesforce `multipicklist` → PostgreSQL `Text`
   - Salesforce `address` → PostgreSQL `JSON`

5. **Index Creation**:
   Strategic indexes are created for common query patterns:
   ```python
   __table_args__ = (
       Index("idx_sf_contact_salesforce_id", "salesforce_id"),
       Index("idx_sf_contact_email", "email"),
       Index("idx_sf_contact_npi", "npi"),
       Index("idx_sf_contact_specialty", "specialty"),
   )
   ```

### Database Migration Process

1. **Schema Changes**: When Salesforce schema changes, run `explore_schemas.py` to generate updated documentation
2. **Model Updates**: Update SQLAlchemy models in `salesforce_data.py` based on schema changes
3. **Migration Generation**: Use Alembic to generate database migrations:
   ```bash
   ./makemigration.sh "Add new Salesforce fields"
   ```
4. **Migration Execution**: Apply migrations to update PostgreSQL schema:
   ```bash
   ./migrate.sh
   ```

## High-Level Functions

### Data Synchronization Flow

1. **Authentication**: Services authenticate with Salesforce using OAuth 2.0
2. **Data Extraction**: 
   - REST API: Execute SOQL queries for smaller datasets
   - Bulk API: Create bulk jobs for large datasets
3. **Data Transformation**: Convert Salesforce data to PostgreSQL format
4. **Data Loading**: Use upsert operations to handle new/updated records
5. **Monitoring**: Log operations and track performance metrics

### Common Patterns

All sync services follow these patterns:

```python
# 1. Initialize with database session and Salesforce service
sync_service = SyncService(db_session, sf_service)

# 2. Execute sync with optional parameters
stats = sync_service.sync_objects(
    modified_since=datetime.now() - timedelta(days=7),
    limit=1000
)

# 3. Return comprehensive statistics
{
    "total_retrieved": 1000,
    "total_processed": 995,
    "new_records": 50,
    "updated_records": 945,
    "errors": 5
}
```

### Error Handling and Resilience

- **Retry Logic**: Automatic retry for transient failures
- **Batch Processing**: Large datasets processed in manageable chunks
- **Progress Tracking**: Detailed logging for monitoring and debugging
- **Graceful Degradation**: Continue processing even if individual records fail
- **Data Validation**: Validate data before database operations

## Performance Characteristics

| Service | API Type | Typical Dataset | Sync Time | Best Use Case |
|---------|----------|-----------------|-----------|---------------|
| Contact Sync (Bulk) | Bulk API 2.0 | 600K+ records | 10-15 minutes | Full sync, large datasets |
| Contact Sync (REST) | REST API | <50K records | 5-10 minutes | Incremental sync, testing |
| Activity Sync | REST API | 100K+ records | 15-20 minutes | Task/Event sync |
| User Sync | REST API | <10K records | 2-3 minutes | User profile sync |
| TaskWhoRelation Sync | REST API | 500K+ records | 20-30 minutes | Relationship sync |
| Targeted Sync | Hybrid | 50K+ active contacts | 5-8 minutes | Active contact focus |

## Usage Examples

### Full Contact Sync
```bash
cd app/services/salesforce_files/contact_sync
python run_contact_sync.py --mode bulk --full
```

### Incremental Activity Sync
```bash
cd app/services/salesforce_files/activity_sync
python run_activity_sync.py --days 7
```

### Schema Exploration
```bash
cd app/services/salesforce_files/schema_docs
python explore_schemas.py
```

### Monitoring and Logs
```bash
# View recent sync logs
tail -f app/services/salesforce_files/logs/contact_sync.log

# Check API usage
python -c "from salesforce_monitoring import SalesforceMonitoring; print(SalesforceMonitoring().get_usage_summary())"
```

## Development Guidelines

1. **Extend Base Services**: Always use `salesforce_service.py` or `bulk_salesforce_service.py` as foundation
2. **Follow Patterns**: Use established patterns for authentication, error handling, and logging
3. **Document Schema**: Update schema documentation when adding new objects
4. **Test Thoroughly**: Use test modes and small datasets for development
5. **Monitor Performance**: Track sync times and optimize for large datasets
6. **Handle Errors Gracefully**: Implement retry logic and detailed error reporting

## Security and Compliance

- **Read-Only Operations**: All sync services are read-only to prevent accidental data modification
- **Credential Management**: Use environment variables for sensitive credentials
- **Audit Logging**: All operations are logged for audit and debugging purposes
- **Rate Limiting**: Respect Salesforce API limits to avoid service disruption

This architecture provides a robust, scalable foundation for Salesforce data integration while maintaining clear separation of concerns and comprehensive monitoring capabilities. 