# Relationship Manager Architecture

## Overview

The Relationship Manager is a comprehensive CRM feature designed to help physician liaisons track and manage their relationships with healthcare providers, practices, and facilities. This document describes the complete architecture including backend services, APIs, database design, and the single-page application (SPA) frontend.

## Table of Contents

1. [Database Architecture](#database-architecture)
2. [Backend Services](#backend-services)
3. [RESTful API Endpoints](#restful-api-endpoints)
4. [Frontend Architecture](#frontend-architecture)
5. [Data Flow & Interactions](#data-flow--interactions)
6. [Key Features](#key-features)
7. [Security & Performance](#security--performance)

## Database Architecture

### Core Tables

#### 1. `relationships`
Primary table storing all user-entity relationships.

```sql
- relationship_id (UUID): Primary key
- user_id (INT): Reference to sf_user
- entity_type_id (INT): Reference to entity_types lookup
- linked_entity_id (UUID): ID of the related entity
- relationship_status_id (INT): Current relationship status
- loyalty_status_id (INT): Current loyalty status (nullable)
- lead_score (INT 1-5): Scoring for prioritization
- last_activity_date (TIMESTAMP): Most recent interaction
- next_steps (TEXT): Action items for this relationship
- engagement_frequency (VARCHAR): Expected interaction cadence
- created_at, updated_at: Timestamps
```

#### 2. `campaigns`
Marketing and outreach campaign definitions.

```sql
- campaign_id (UUID): Primary key
- campaign_name (VARCHAR): Display name
- description (TEXT): Campaign details
- status (VARCHAR): Active/Inactive/Completed
- campaign_type (VARCHAR): Type classification
- start_date, end_date: Campaign duration
- target_audience (JSONB): Criteria for targeting
- goals (JSONB): Success metrics
- owner_id (INT): Campaign manager
```

#### 3. `campaign_relationships`
Many-to-many junction table linking campaigns to relationships.

```sql
- campaign_id (UUID): Reference to campaigns
- relationship_id (UUID): Reference to relationships
- enrollment_date: When relationship joined campaign
- status: Enrolled/Completed/Dropped
- notes: Campaign-specific notes
```

#### 4. `relationship_history`
Audit trail for relationship status changes.

```sql
- history_id (SERIAL): Primary key
- relationship_id (UUID): Reference to relationships
- changed_by_user_id (INT): User who made the change
- change_date (TIMESTAMP): When change occurred
- previous_relationship_status: Status before change
- new_relationship_status: Status after change
- previous_loyalty: Loyalty before change
- new_loyalty: Loyalty after change
- change_reason: Explanation for change
```

#### 5. `relationship_metrics`
Time-series metrics for relationship analytics.

```sql
- metric_id (SERIAL): Primary key
- relationship_id (UUID): Reference to relationships
- metric_date (DATE): Date of metrics calculation
- meetings_count: Number of meetings
- calls_count: Number of calls
- emails_count: Number of emails
- referrals_count: Number of referrals received
- response_time_avg: Average response time in hours
```

### Lookup Tables

#### 1. `entity_types`
Defines the types of entities that can have relationships.

```sql
- id (SERIAL): Primary key
- code (VARCHAR): System code (e.g., 'SfContact', 'ClaimsProvider')
- common_name (VARCHAR): Display name
- description (TEXT): Detailed description
- source_table (VARCHAR): Database table name
- is_active (BOOLEAN): Whether type is currently in use
- sort_order (INT): Display ordering
```

#### 2. `relationship_status_types`
Defines possible relationship statuses.

```sql
- id (SERIAL): Primary key
- code (VARCHAR): System code
- display_name (VARCHAR): User-friendly name
- description (TEXT): When to use this status
- is_active (BOOLEAN): Whether available for selection
- sort_order (INT): Display ordering

Default Values:
1. ESTABLISHED - Strong, ongoing relationship
2. BUILDING - Developing relationship
3. PROSPECTING - Initial outreach phase
4. DEPRIORITIZED - Inactive or low priority
```

#### 3. `loyalty_status_types`
Defines loyalty/referral status classifications.

```sql
- id (SERIAL): Primary key
- code (VARCHAR): System code
- display_name (VARCHAR): User-friendly name
- description (TEXT): Status description
- color_hex (VARCHAR): UI color for visual distinction
- is_active (BOOLEAN): Whether available
- sort_order (INT): Display ordering

Default Values:
1. LOYAL - Consistently refers to our system
2. AT_RISK - Showing signs of switching
3. NEUTRAL - No clear loyalty pattern
```

## Backend Services

### 1. RelationshipService (`/app/services/relationship_service.py`)

Core business logic service handling all relationship operations.

#### Key Methods:

**`list_relationships(filters, page, page_size, sort_by, sort_order)`**
- Retrieves paginated list of relationships with complex filtering
- Supports filtering by: users, entity types, statuses, scores, dates, geography, specialties
- Eager loads related data for performance
- Returns enriched relationship data with calculated metrics

**`get_relationship_detail(relationship_id)`**
- Fetches complete relationship information
- Includes: entity details, recent activities, metrics, campaigns
- Calculates real-time metrics from activity data

**`update_relationship(relationship_id, updates, user_id)`**
- Updates relationship fields (status, score, next steps)
- Creates audit trail in relationship_history
- Validates status transitions

**`get_filter_options(current_user_id)`**
- Returns all available filter options for UI dropdowns
- Includes counts for better UX
- Dynamically pulls specialties, geographies from data

**Private Helper Methods:**
- `_apply_filters()`: SQL query builder for complex filtering
- `_get_entity_details()`: Polymorphic entity data retrieval
- `_get_recent_activities()`: Activity log aggregation
- `_calculate_metrics()`: Real-time metrics calculation

### 2. RelationshipSeedingService (`/app/services/relationship_seeding_service.py`)

One-time service for initial data population from historical activities.

#### Business Rules:
- **Relationship Status Calculation**:
  - ESTABLISHED: >5 activities in last 90 days
  - BUILDING: 2-5 activities in last 90 days
  - PROSPECTING: 1 activity in last 90 days
  - DEPRIORITIZED: No activity in 180+ days

- **Lead Score Calculation**:
  - Based on: frequency, recency, priority level, employment status
  - Community contacts get +1 boost (growth opportunities)
  - Scoring algorithm weights recent activities higher

- **Employment Status Handling**:
  - "Employed" = Internal health system physicians
  - "Community" = External/out-of-network providers
  - Impacts lead scoring and prioritization

## RESTful API Endpoints

### Base URL: `/api/relationships`

#### 1. **GET /** - List Relationships
Retrieves paginated list with filtering and sorting.

**Query Parameters:**
```
- page (int): Page number (default: 1)
- page_size (int): Items per page (default: 50, max: 100)
- sort_by (string): Sort field (last_activity_date|entity_name|relationship_status|lead_score)
- sort_order (string): asc|desc (default: desc)

Filters:
- user_ids[] (int): Filter by specific users
- my_relationships_only (bool): Current user's relationships only
- entity_type_ids[] (int): Filter by entity types
- entity_ids[] (uuid): Specific entities
- relationship_status_ids[] (int): Status filters
- loyalty_status_ids[] (int): Loyalty filters
- lead_scores[] (int): Score filters (1-5)
- last_activity_after (date): Activity date range start
- last_activity_before (date): Activity date range end
- days_since_activity_min (int): Minimum days since activity
- days_since_activity_max (int): Maximum days since activity
- campaign_ids[] (uuid): Associated campaigns
- search_text (string): Search in names and notes
- geographies[] (string): Geographic filters
- cities[] (string): City filters
- specialties[] (string): Specialty filters
```

**Response:**
```json
{
  "items": [
    {
      "relationship_id": "uuid",
      "user_id": 123,
      "user_name": "John Smith",
      "entity_type": {
        "id": 1,
        "code": "SfContact",
        "common_name": "Contact"
      },
      "linked_entity_id": "uuid",
      "entity_name": "Dr. Jane Doe",
      "entity_details": {
        "email": "jane@example.com",
        "phone": "555-0123",
        "specialty": "Cardiology",
        "geography": "North Region"
      },
      "relationship_status": {
        "id": 1,
        "code": "ESTABLISHED",
        "display_name": "Established"
      },
      "loyalty_status": {
        "id": 1,
        "code": "LOYAL",
        "display_name": "Loyal",
        "color_hex": "#28a745"
      },
      "lead_score": 4,
      "last_activity_date": "2024-01-15T10:30:00",
      "days_since_activity": 5,
      "engagement_frequency": "Weekly",
      "activity_count": 25,
      "campaign_count": 2,
      "next_steps": "Schedule quarterly review",
      "created_at": "2023-06-01T08:00:00",
      "updated_at": "2024-01-15T10:30:00"
    }
  ],
  "total_count": 859,
  "page": 1,
  "page_size": 50,
  "total_pages": 18
}
```

#### 2. **GET /filter-options** - Get Filter Options
Returns all available options for filter dropdowns.

**Response:**
```json
{
  "users": [
    {
      "id": 123,
      "name": "John Smith",
      "relationship_count": 45
    }
  ],
  "entity_types": [
    {
      "id": 1,
      "code": "SfContact",
      "common_name": "Contact"
    }
  ],
  "relationship_statuses": [
    {
      "id": 1,
      "code": "ESTABLISHED",
      "display_name": "Established"
    }
  ],
  "loyalty_statuses": [
    {
      "id": 1,
      "code": "LOYAL",
      "display_name": "Loyal",
      "color_hex": "#28a745"
    }
  ],
  "campaigns": [
    {
      "id": "uuid",
      "name": "Q1 Cardiology Outreach"
    }
  ],
  "geographies": ["North Region", "South Region"],
  "specialties": ["Cardiology", "Orthopedics", "Primary Care"]
}
```

#### 3. **GET /{relationship_id}** - Get Relationship Detail
Fetches complete information for a single relationship.

**Response:**
```json
{
  "relationship_id": "uuid",
  "user_id": 123,
  "user_name": "John Smith",
  "user_email": "john@health.org",
  "entity_type": { /* same as list */ },
  "linked_entity_id": "uuid",
  "entity_name": "Dr. Jane Doe",
  "entity_details": {
    "email": "jane@example.com",
    "phone": "555-0123",
    "specialty": "Cardiology",
    "account": "Heart Associates",
    "geography": "North Region",
    "title": "Chief of Cardiology"
  },
  "relationship_status": { /* same as list */ },
  "loyalty_status": { /* same as list */ },
  "lead_score": 4,
  "last_activity_date": "2024-01-15T10:30:00",
  "next_steps": "Schedule quarterly review",
  "engagement_frequency": "Weekly",
  "campaigns": [
    {
      "campaign_id": "uuid",
      "campaign_name": "Q1 Cardiology Outreach",
      "status": "Active",
      "start_date": "2024-01-01",
      "end_date": "2024-03-31"
    }
  ],
  "metrics": {
    "total_activities": 125,
    "activities_last_30_days": 12,
    "activities_last_90_days": 35,
    "average_days_between_activities": 7.5,
    "most_common_activity_type": "Meeting",
    "last_activity_days_ago": 5,
    "referral_count": 8,
    "meeting_count": 45,
    "call_count": 30,
    "email_count": 50
  },
  "recent_activities": [
    {
      "activity_id": "uuid",
      "activity_date": "2024-01-15T10:30:00",
      "subject": "Quarterly Business Review",
      "description": "Discussed referral patterns...",
      "activity_type": "Meeting",
      "mno_type": "Meeting",
      "mno_subtype": "In-Person",
      "status": "Completed",
      "owner_name": "John Smith",
      "contact_names": ["Dr. Jane Doe", "Office Manager"]
    }
  ],
  "created_at": "2023-06-01T08:00:00",
  "updated_at": "2024-01-15T10:30:00"
}
```

#### 4. **PATCH /{relationship_id}** - Update Relationship
Updates specific fields of a relationship.

**Request Body:**
```json
{
  "relationship_status_id": 1,
  "loyalty_status_id": 2,
  "lead_score": 5,
  "next_steps": "Follow up on referral program enrollment",
  "engagement_frequency": "Monthly"
}
```

**Response:** Returns updated relationship detail (same as GET detail)

#### 5. **POST /bulk-update** - Bulk Update Relationships
Updates multiple relationships with the same changes.

**Request Body:**
```json
{
  "relationship_ids": ["uuid1", "uuid2", "uuid3"],
  "updates": {
    "relationship_status_id": 2,
    "lead_score": 3
  }
}
```

**Response:**
```json
{
  "updated_count": 3,
  "relationships": [ /* array of updated relationships */ ],
  "message": "Successfully updated 3 relationships"
}
```

#### 6. **GET /{relationship_id}/activities** - Get Activities
Retrieves activity history for a relationship.

**Query Parameters:**
- page (int): Page number
- page_size (int): Items per page (max: 50)

**Response:**
```json
{
  "activities": [ /* array of activity items */ ],
  "total_count": 125,
  "page": 1,
  "page_size": 20
}
```

#### 7. **POST /{relationship_id}/activities** - Log Activity
Creates a new activity log entry (currently not implemented).

#### 8. **GET /{relationship_id}/metrics** - Get Metrics
Returns detailed metrics and analytics for a relationship.

#### 9. **POST /export** - Export Relationships
Exports filtered relationships to CSV or Excel (currently not implemented).

## Frontend Architecture

### Single-Page Application Structure

The Relationship Manager is built as a React-based SPA with TypeScript for type safety.

#### Component Hierarchy

```
RelationshipManager (Main Container)
├── RelationshipFilters (Left Panel)
│   ├── User Filters
│   ├── Status Filters
│   ├── Activity Date Filters
│   ├── Entity Type Filters
│   ├── Location Filters
│   ├── Specialty Filters
│   └── Campaign Filters
├── RelationshipList (Middle Panel)
│   ├── Bulk Actions Bar
│   ├── Data Table
│   │   ├── Sortable Headers
│   │   ├── Row Selection
│   │   └── Click-to-Detail
│   └── Pagination Controls
└── RelationshipDetail (Right Panel)
    ├── Header with Edit Controls
    ├── Tab Navigation
    │   ├── Overview Tab
    │   │   ├── Status Grid
    │   │   ├── Contact Information
    │   │   ├── Activity Metrics
    │   │   └── Next Steps
    │   ├── Activities Tab
    │   │   └── ActivityTimeline
    │   └── Campaigns Tab
    └── Save/Cancel Actions
```

### State Management

The application uses React's built-in state management with a centralized state in the RelationshipManager component:

```typescript
interface RelationshipManagerState {
  filters: RelationshipFilters;           // Active filter selections
  relationships: RelationshipListItem[];   // Current page of relationships
  selectedRelationship?: RelationshipDetail; // Selected item details
  filterOptions?: FilterOptionsResponse;   // Available filter options
  loading: boolean;                       // Loading states
  error?: string;                         // Error messages
  tableState: RelationshipTableState;     // Table-specific state
  rightPanelOpen: boolean;                // Detail panel visibility
}
```

### Service Layer

The frontend uses a dedicated service layer (`relationshipService.ts`) that:
- Encapsulates all API calls
- Handles request/response transformation
- Provides typed methods for each endpoint
- Includes utility methods (e.g., downloadExport)

### Key Frontend Features

1. **Advanced Filtering**
   - Multi-select filters with counts
   - Date range pickers
   - Text search
   - Clear all functionality
   - Collapsible filter sections

2. **Data Table**
   - Sortable columns
   - Bulk selection with Select All
   - Inline status badges with colors
   - Star ratings for lead scores
   - Click-to-view details

3. **Inline Editing**
   - Edit mode toggle
   - Form validation
   - Optimistic updates
   - Save/Cancel workflow

4. **Responsive Design**
   - Desktop: Three-panel layout
   - Tablet: Collapsible side panels
   - Mobile: Stacked layout with overlays

## Data Flow & Interactions

### 1. Initial Page Load

```
1. RelationshipManager component mounts
2. Parallel API calls:
   - GET /api/relationships (first page of data)
   - GET /api/relationships/filter-options
3. State updates trigger re-renders
4. Child components receive props
```

### 2. Filtering Flow

```
1. User selects filter in RelationshipFilters
2. onChange handler updates parent state
3. useEffect triggers new API call with filters
4. Results update in RelationshipList
5. Pagination resets to page 1
```

### 3. Detail View Flow

```
1. User clicks relationship in list
2. onRelationshipSelect handler called
3. GET /api/relationships/{id} fetches details
4. Right panel opens with RelationshipDetail
5. Activity timeline loads recent activities
```

### 4. Edit/Update Flow

```
1. User clicks Edit in detail panel
2. Form fields become editable
3. User makes changes
4. Save triggers PATCH /api/relationships/{id}
5. Success response updates both:
   - Detail view (immediate)
   - List view (updated item)
```

### 5. Bulk Operations Flow

```
1. User selects multiple relationships
2. Bulk actions bar appears
3. User selects new status/score
4. Apply triggers POST /api/relationships/bulk-update
5. Success triggers full list refresh
```

## Key Features

### 1. Smart Relationship Scoring
- Algorithm considers activity frequency, recency, and type
- Community providers get scoring boost (growth opportunity)
- Automatic status transitions based on activity patterns

### 2. Activity-Based Insights
- Real-time metrics calculation from activity logs
- Historical tracking via relationship_metrics table
- Visual timeline with expandable details

### 3. Campaign Integration
- Track which relationships are part of campaigns
- Filter by campaign participation
- View campaign details in relationship context

### 4. Audit Trail
- Complete history of status changes
- Who changed what and when
- Change reasons captured

### 5. Flexible Entity Support
- Polymorphic relationships to multiple entity types
- Currently supports: SfContacts, ClaimsProviders, SiteOfService
- Extensible to new entity types via lookup table

## Security & Performance

### Security Measures
1. **Authentication**: User context required for all operations
2. **Authorization**: Filter by user ownership (my_relationships_only)
3. **Audit Trail**: All changes tracked with user attribution
4. **Input Validation**: Pydantic schemas validate all inputs

### Performance Optimizations
1. **Eager Loading**: Related data loaded in single query
2. **Pagination**: Large datasets handled efficiently
3. **Indexed Columns**: Database indexes on filter fields
4. **Caching**: Filter options cached on frontend
5. **Debouncing**: Search input debounced to reduce API calls

### Scalability Considerations
1. **Horizontal Scaling**: Stateless API design
2. **Database Connection Pooling**: Via SQLAlchemy
3. **Async Operations**: FastAPI async endpoints
4. **Batch Operations**: Bulk updates reduce API calls

## Future Enhancements

### Planned Features
1. **Real-time Updates**: WebSocket integration for live updates
2. **Advanced Analytics**: Relationship trends and predictions
3. **LLM Integration**: AI-powered insights and recommendations
4. **Export Functionality**: CSV/Excel export with filters
5. **Mobile App**: Native mobile experience

### API Extensions
1. **Activity Logging**: POST endpoint implementation
2. **File Attachments**: Document storage per relationship
3. **Team Collaboration**: Shared relationships and notes
4. **Workflow Automation**: Trigger-based status updates
5. **Third-party Integrations**: CRM and calendar sync