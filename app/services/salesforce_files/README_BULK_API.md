# Salesforce Bulk API Contact Sync

This directory contains a comprehensive solution for syncing large volumes of contact data from Salesforce using the **Salesforce Bulk API 2.0**. This approach is specifically designed to handle 600,000+ contacts efficiently.

## 🚀 Why Bulk API vs REST API?

| Feature | REST API | Bulk API 2.0 |
|---------|----------|---------------|
| **Record Limit** | ~2,000 per query | Millions |
| **Processing Time** | Sequential | Parallel/Asynchronous |
| **API Call Efficiency** | 1 call per batch | 1 call per job |
| **Memory Usage** | High (loads all in memory) | Low (streaming) |
| **Best For** | <10,000 records | 10,000+ records |

## 📁 File Structure

```
salesforce_files/
├── bulk_salesforce_service.py          # Core Bulk API service
├── bulk_contact_sync_service.py        # Contact-specific sync logic
├── production_contact_sync_bulk.py     # Main production sync script
├── test_bulk_connection.py             # Test connection and estimate sync time
└── README_BULK_API.md                  # This file
```

## 🔧 Setup Requirements

### 1. Environment Variables
Ensure these environment variables are set:

```bash
SALESFORCE_USERNAME=your_username@company.com
SALESFORCE_PASSWORD=your_password
SALESFORCE_SECURITY_TOKEN=your_security_token
SALESFORCE_DOMAIN=login  # or 'test' for sandbox
```

### 2. Dependencies
The bulk API solution requires these additional Python packages:

```bash
pip install requests python-dotenv
```

## 🎯 Usage Options

### Option 1: Test Connection First (Recommended)
Before running a full sync, test your connection:

```bash
# Test bulk API connection and get estimates
python app/services/salesforce_files/test_bulk_connection.py
```

This will:
- ✅ Verify authentication
- 📊 Check API limits  
- ⏱️ Estimate sync time for your dataset
- 🔍 Show sample contact data

### Option 2: Run Full Sync
Sync all contacts from Salesforce:

```bash
# Full sync of all contacts
python app/services/salesforce_files/production_contact_sync_bulk.py --full
```

### Option 3: Incremental Sync
Sync only recently modified contacts:

```bash
# Sync contacts modified in last 7 days
python app/services/salesforce_files/production_contact_sync_bulk.py --incremental 7

# Sync contacts modified in last 30 days
python app/services/salesforce_files/production_contact_sync_bulk.py --incremental 30
```

### Option 4: Test Connection Only
Quick connection test:

```bash
python app/services/salesforce_files/production_contact_sync_bulk.py --test
```

## 📊 Expected Performance

Based on typical Salesforce Bulk API performance:

| Dataset Size | Estimated Time | Processing Rate |
|--------------|----------------|-----------------|
| 10,000 contacts | 2-3 minutes | ~3,000/minute |
| 100,000 contacts | 20-30 minutes | ~3,000/minute |
| 600,000 contacts | 2-3 hours | ~3,000/minute |
| 1,000,000 contacts | 3-5 hours | ~3,000/minute |

*Note: Times can vary based on field complexity and Salesforce server load*

## 🔍 What Gets Synced

The bulk sync extracts **90+ fields** per contact, including:

### Standard Fields
- Core identity (Name, Email, Phone, etc.)
- Mailing address information
- Activity tracking dates

### Custom Fields (Minnesota-specific)
- Provider information (NPI, Specialty, etc.)
- Network and practice location data
- Geographic and demographic data
- Minnesota-specific address components

## 💾 Database Operations

The sync uses **efficient bulk database operations**:

- **Batch Processing**: Processes 1,000 contacts per database transaction
- **Upsert Operations**: Uses PostgreSQL's `ON CONFLICT` for efficient updates
- **Memory Management**: Processes data in chunks to avoid memory issues
- **Error Handling**: Continues processing even if individual records fail

## 📈 Monitoring & Logging

All operations are logged to:
- **Console**: Real-time progress updates
- **Log File**: `bulk_contact_sync.log` with detailed information

### Sample Log Output
```
2025-07-05 15:30:00,123 - INFO - Starting BULK contact sync
2025-07-05 15:30:01,234 - INFO - ✅ Created bulk query job: 7506D000000XXXXX
2025-07-05 15:30:15,456 - INFO - 📊 Job 7506D000000XXXXX - State: InProgress, Records Processed: 50,000
2025-07-05 15:35:22,789 - INFO - ✅ Job completed! Total records: 600,000
2025-07-05 15:36:45,012 - INFO - Processed batch 1: 1000 records
```

## ⚡ Performance Optimizations

### 1. Efficient Query Design
- Filters out deleted records (`WHERE IsDeleted = FALSE`)
- Orders by `CreatedDate` for consistent processing
- Selects only required fields

### 2. Database Optimizations  
- Bulk upsert operations using PostgreSQL `ON CONFLICT`
- Batch processing to reduce transaction overhead
- Proper indexing on `salesforce_id` for fast lookups

### 3. Memory Management
- Processes data in configurable batches (default: 1,000)
- Streams CSV data instead of loading everything in memory
- Commits transactions in batches

### 4. Error Resilience
- Individual record errors don't stop the entire sync
- Detailed error logging for troubleshooting
- Graceful handling of API limits and timeouts

## 🔧 Configuration Options

### Batch Size
Adjust the batch size for database operations:

```python
# In production_contact_sync_bulk.py
stats = bulk_sync_service.bulk_sync_contacts(
    batch_size=1000  # Increase for better performance, decrease if memory issues
)
```

### API Timeout
Adjust the timeout for bulk jobs:

```python
# In bulk_salesforce_service.py
def wait_for_job_completion(self, job_id: str, max_wait_time: int = 3600):
    # max_wait_time in seconds (default: 1 hour)
```

## 🚨 Troubleshooting

### Authentication Issues
```
❌ Bulk API authentication failed: invalid_grant
```
**Solution**: Check your username, password, and security token

### Job Timeout
```
⏰ Job did not complete within 3600 seconds
```
**Solution**: Increase `max_wait_time` or reduce query complexity

### Memory Issues
```
MemoryError: Unable to allocate array
```
**Solution**: Reduce `batch_size` in the sync configuration

### API Limits
```
❌ Daily API request limit exceeded
```
**Solution**: Check your API limits or schedule sync during off-peak hours

## 📋 Migration from REST API

If you're currently using the REST API sync (`production_contact_sync.py`), here's the migration path:

### 1. Test First
```bash
python app/services/salesforce_files/test_bulk_connection.py
```

### 2. Compare Results
Run both syncs on a subset and compare:

```bash
# Old method (limited)
python app/services/salesforce_files/production_contact_sync.py

# New method (full dataset)
python app/services/salesforce_files/production_contact_sync_bulk.py --full
```

### 3. Switch to Bulk API
Once verified, use the bulk API for all future syncs.

## 🔮 Future Enhancements

Potential improvements for the bulk sync system:

1. **Parallel Job Processing**: Split large datasets into multiple parallel jobs
2. **Resume Capability**: Resume failed syncs from the last successful batch
3. **Field Selection**: Allow dynamic field selection to reduce data transfer
4. **Compression**: Add data compression for faster transfer
5. **Scheduling**: Add cron-like scheduling for automatic syncs

## 📞 Support

For issues with the bulk sync:

1. Check the log files for detailed error messages
2. Run the connection test to verify setup
3. Review Salesforce API limits and usage
4. Ensure all environment variables are correctly set

---

*This bulk API solution is designed to handle enterprise-scale Salesforce data synchronization efficiently and reliably.* 