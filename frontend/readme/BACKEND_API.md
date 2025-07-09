# Backend API Documentation

## Overview

The backend API is a FastAPI-based service that provides RESTful endpoints for managing sales activity data. It serves as the core data layer for the Cool Mint activity selector system, offering efficient querying, filtering, and data processing capabilities.

## Technology Stack

- **FastAPI**: Modern Python web framework with automatic API documentation
- **SQLAlchemy**: Database ORM for PostgreSQL integration
- **Pydantic**: Data validation and serialization
- **PostgreSQL**: Primary database with Supabase integration
- **Redis**: Caching and session management
- **Celery**: Background task processing

## API Architecture

### Base URL
- Development: `http://localhost:8080/api/activities/`
- Production: `https://your-domain.com/api/activities/`

### Authentication
Currently bypassing Kong authentication for development. Direct FastAPI access with CORS enabled for `localhost:3000`.

## Core Endpoints

### GET /activities/
List activities with filtering and pagination support.

**Parameters:**
- `page` (int): Page number (default: 1)
- `page_size` (int): Items per page (default: 50, max: 100)
- `sort_by` (str): Sort field (default: "activity_date")
- `sort_order` (str): Sort direction "asc" or "desc" (default: "desc")
- `owner_ids` (list): Filter by activity owner IDs
- `start_date` (str): Filter activities after this date (ISO format)
- `end_date` (str): Filter activities before this date (ISO format)
- `search_text` (str): Search in subject and description
- `has_contact` (bool): Filter by contact presence
- `has_md_contact` (bool): Filter by MD contact presence
- `has_pharma_contact` (bool): Filter by pharma contact presence
- `contact_specialties` (list): Filter by contact specialties
- `mno_types` (list): Filter by MNO activity types
- `mno_subtypes` (list): Filter by MNO activity subtypes
- `statuses` (list): Filter by activity statuses
- `types` (list): Filter by activity types

**Response:**
```json
{
  "activities": [
    {
      "id": "uuid-string",
      "activity_id": "salesforce-id",
      "activity_date": "2024-01-15T10:30:00Z",
      "subject": "Meeting with Dr. Smith",
      "description": "Discussed new treatment options...",
      "owner_name": "John Doe",
      "owner_id": "owner-uuid",
      "type": "Meeting",
      "mno_type": "HCP Engagement",
      "mno_subtype": "Face-to-face",
      "status": "Completed",
      "contact_count": 2,
      "contact_names": ["Dr. Smith", "Nurse Johnson"],
      "contact_specialties": ["Cardiology", "Nursing"],
      "has_md_contact": true,
      "has_pharma_contact": false
    }
  ],
  "total_count": 1277,
  "page": 1,
  "page_size": 50,
  "total_pages": 26
}
```

### GET /activities/filter-options
Get available values for filter dropdowns.

**Response:**
```json
{
  "owners": [
    {"id": "uuid", "name": "John Doe", "activity_count": 45},
    {"id": "uuid", "name": "Jane Smith", "activity_count": 32}
  ],
  "types": ["Meeting", "Call", "Email", "Event"],
  "mno_types": ["HCP Engagement", "Market Research", "Training"],
  "mno_subtypes": ["Face-to-face", "Virtual", "Phone"],
  "statuses": ["Completed", "Pending", "Cancelled"],
  "specialties": ["Cardiology", "Oncology", "Neurology", "Pulmonology"]
}
```

### POST /activities/selection
Process selected activities for LLM sharing.

**Request:**
```json
{
  "activity_ids": ["uuid1", "uuid2", "uuid3"]
}
```

**Response:**
```json
{
  "message": "Successfully processed 3 activities",
  "processed_count": 3,
  "processing_id": "process-uuid"
}
```

### GET /activities/{activity_id}
Get detailed information for a specific activity.

**Response:**
```json
{
  "id": "uuid-string",
  "activity_id": "salesforce-id",
  "activity_date": "2024-01-15T10:30:00Z",
  "subject": "Meeting with Dr. Smith",
  "description": "Detailed description of the meeting...",
  "owner_name": "John Doe",
  "owner_id": "owner-uuid",
  "type": "Meeting",
  "mno_type": "HCP Engagement",
  "mno_subtype": "Face-to-face",
  "status": "Completed",
  "contacts": [
    {
      "name": "Dr. Smith",
      "title": "Cardiologist",
      "specialty": "Cardiology",
      "is_md": true,
      "is_pharma": false
    }
  ],
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

## Data Models

### ActivityListItem
```python
class ActivityListItem(BaseModel):
    id: str
    activity_id: str
    activity_date: datetime
    subject: str
    description: Optional[str] = None
    owner_name: Optional[str] = None
    owner_id: Optional[str] = None
    type: Optional[str] = None
    mno_type: Optional[str] = None
    mno_subtype: Optional[str] = None
    status: Optional[str] = None
    contact_count: int = 0
    contact_names: List[str] = []
    contact_specialties: List[str] = []
    has_md_contact: bool = False
    has_pharma_contact: bool = False
```

### ActivityFilters
```python
class ActivityFilters(BaseModel):
    owner_ids: Optional[List[str]] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    search_text: Optional[str] = None
    has_contact: Optional[bool] = None
    has_md_contact: Optional[bool] = None
    has_pharma_contact: Optional[bool] = None
    contact_specialties: Optional[List[str]] = None
    mno_types: Optional[List[str]] = None
    mno_subtypes: Optional[List[str]] = None
    statuses: Optional[List[str]] = None
    types: Optional[List[str]] = None
```

## Database Schema

### SfActivityStructured Table
The primary data source with the following key fields:

- `id`: UUID primary key
- `salesforce_activity_id`: Salesforce record ID
- `activity_date`: Date and time of activity
- `subject`: Activity subject line
- `description`: Detailed activity description
- `user_name`: Activity owner name
- `user_id`: Activity owner ID
- `type`: Basic activity type
- `mno_type`: MNO categorization
- `mno_subtype`: MNO subcategorization
- `status`: Activity status
- `contact_count`: Number of associated contacts
- `contact_names`: JSON array of contact names
- `contact_specialties`: JSON array of specialties
- `has_md_contact`: Boolean for MD presence
- `has_pharma_contact`: Boolean for pharma presence

## Query Optimization

### Indexing Strategy
- Primary index on `id` (UUID)
- Index on `activity_date` for date range queries
- Index on `user_id` for owner filtering
- Composite index on `(activity_date, user_id)` for common queries
- Full-text search index on `subject` and `description`

### Pagination
- Efficient limit/offset pagination
- Count queries optimized with EXISTS
- Configurable page sizes (max 100)

### Filtering Performance
- Parameterized queries to prevent SQL injection
- Optimized WHERE clause construction
- Efficient JSON field queries for arrays

## Error Handling

### HTTP Status Codes
- `200`: Success
- `400`: Bad Request (invalid parameters)
- `404`: Not Found (activity doesn't exist)
- `422`: Validation Error (invalid data format)
- `500`: Internal Server Error

### Error Response Format
```json
{
  "detail": "Error description",
  "error_code": "VALIDATION_ERROR",
  "fields": ["field_name"]
}
```

## CORS Configuration

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Security Features

### Input Validation
- Pydantic model validation for all inputs
- SQL injection prevention with parameterized queries
- XSS protection with output sanitization
- Rate limiting on API endpoints

### Authentication (Future)
- JWT token authentication
- Role-based access control
- API key management
- Session management

## Performance Monitoring

### Metrics Tracked
- Request latency
- Database query performance
- Memory usage
- Error rates

### Logging
- Structured logging with JSON format
- Request/response logging
- Error tracking
- Performance metrics

## Development Setup

### Environment Variables
```bash
DATABASE_HOST=localhost
DATABASE_NAME=postgres
DATABASE_USER=postgres
DATABASE_PASSWORD=password
DATABASE_PORT=5432
REDIS_URL=redis://localhost:6379
```

### Database Migration
```bash
# Generate migration
alembic revision --autogenerate -m "Add activity table"

# Apply migration
alembic upgrade head
```

### Testing
```bash
# Run unit tests
pytest app/tests/

# Run integration tests
pytest app/tests/integration/

# Test API endpoints
./test-activity-api.sh
```

## Deployment

### Docker Configuration
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app/ .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### Production Considerations
- Connection pooling for PostgreSQL
- Redis clustering for high availability
- Load balancing for multiple instances
- SSL/TLS termination
- Monitoring and alerting

## API Documentation

### Swagger UI
Available at: `http://localhost:8080/docs`

### ReDoc
Available at: `http://localhost:8080/redoc`

### OpenAPI Schema
Available at: `http://localhost:8080/openapi.json`

## Future Enhancements

### Planned Features
- GraphQL endpoint for flexible queries
- Real-time updates with WebSocket
- Advanced analytics endpoints
- Bulk operations API
- Export functionality

### Performance Improvements
- Query result caching
- Database connection pooling
- Async database operations
- Response compression

## Troubleshooting

### Common Issues

1. **Database Connection Issues**
   - Check PostgreSQL service status
   - Verify connection string format
   - Check firewall settings

2. **Slow Query Performance**
   - Review database indexes
   - Analyze query execution plans
   - Check for N+1 query problems

3. **Memory Usage**
   - Monitor large result sets
   - Implement pagination limits
   - Check for memory leaks

### Debug Mode
Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

*For additional technical details, refer to the source code in `/app/api/activities.py` and related modules.*