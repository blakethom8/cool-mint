# Monthly Activity Summary Workflow - Development Plan

## Overview
Build a workflow that generates monthly activity summaries for users by pulling data from the Salesforce database, structuring it for LLM analysis, and creating comprehensive summaries of outreach activities.

## Architecture Overview
```
[User Request] -> [Category Node] -> [SQL Data Node] -> [Data Structure Node] -> [LLM Summary Node] -> [Response]
```

## Components to Build

### 1. Schema Definition
- **File**: `app/schemas/monthly_activity_summary_schema.py`
- **Purpose**: Define the event schema for monthly activity summary requests
- **Fields**: `user_id`, `start_date`, `end_date`, `request_type`
- **Status**: ⏳ Pending

### 2. Workflow Nodes Directory
- **Directory**: `app/workflows/monthly_activity_summary_nodes/`
- **Purpose**: Container for all workflow nodes
- **Status**: ⏳ Pending

### 3. Node 1: Request Category Node
- **File**: `app/workflows/monthly_activity_summary_nodes/request_category_node.py`
- **Purpose**: Categorize the request type (hardcoded to "monthly_summary" for now)
- **Type**: Simple classification node
- **Status**: ⏳ Pending

### 4. Node 2: SQL Data Retrieval Node
- **File**: `app/workflows/monthly_activity_summary_nodes/sql_data_node.py`
- **Purpose**: Execute SQL query to retrieve activity data with joins
- **Dependencies**: Database session, SQLAlchemy models
- **Query Features**:
  - Join sf_activities, sf_contacts, sf_users
  - Filter by user_id and date range (past 1 month)
  - Select key fields: activity description, contact name, specialty, activity date
- **Status**: ⏳ Pending

### 5. Node 3: Data Structure Node
- **File**: `app/workflows/monthly_activity_summary_nodes/data_structure_node.py`
- **Purpose**: Structure raw SQL data for LLM consumption
- **Features**:
  - Group activities by provider/specialty
  - Format descriptions for readability
  - Create summary statistics
- **Status**: ⏳ Pending

### 6. Node 4: LLM Summary Node
- **File**: `app/workflows/monthly_activity_summary_nodes/llm_summary_node.py`
- **Purpose**: Generate comprehensive activity summary using OpenAI
- **Type**: AgentNode with custom prompt
- **Features**:
  - Analyze outreach patterns
  - Identify key discussions
  - Highlight focus areas by specialty
  - Provide actionable insights
- **Status**: ⏳ Pending

### 7. Main Workflow
- **File**: `app/workflows/monthly_activity_summary_workflow.py`
- **Purpose**: Orchestrate the complete workflow
- **Status**: ⏳ Pending

### 8. Supporting Components

#### SQL Query Templates
- **File**: `app/workflows/monthly_activity_summary_nodes/sql_templates.py`
- **Purpose**: Centralized SQL query definitions
- **Status**: ⏳ Pending

#### Prompt Templates
- **File**: `app/prompts/monthly_activity_summary/activity_summary.yaml`
- **Purpose**: LLM prompt configuration for activity summarization
- **Status**: ⏳ Pending

## Implementation Steps

### Phase 1: Foundation ✅
1. Create schema definition ✅
2. Create workflow nodes directory structure ✅
3. Create SQL templates file ✅
4. Create prompt template file ✅

**Implementation Notes:**
- Created `MonthlyActivitySummaryEvent` schema with user_id, date range, and metadata fields
- Established workflow nodes directory structure with `__init__.py`
- Built comprehensive SQL templates with 4 different query types for activity analysis
- Created OpenAI prompt template focused on healthcare outreach analysis

### Phase 2: Data Layer ✅
1. Build SQL data retrieval node ✅
2. Test database connectivity and query execution ✅
3. Build data structure node ✅
4. Test data formatting and structuring ✅

**Implementation Notes:**
- Created `SQLDataNode` with comprehensive database querying capabilities
- Implemented 4 different SQL queries: main activities, summary stats, specialty breakdown, and contact summary
- Built `DataStructureNode` with advanced data organization features
- Added structured data format with specialty grouping, contact insights, timeline analysis, and key discussions extraction
- Implemented proper error handling and logging throughout the data layer

### Phase 3: Processing Layer ✅
1. Create request category node ✅
2. Build LLM summary node with OpenAI integration ✅
3. Test individual node functionality ✅

**Implementation Notes:**
- Created `RequestCategoryNode` with hardcoded "monthly_summary" classification and extensible architecture
- Built `LLMSummaryNode` using AgentNode pattern with comprehensive output schema
- Integrated OpenAI GPT-4 with specialized prompt for healthcare outreach analysis
- Implemented structured output with 10 key analysis areas including executive summary, specialty insights, and strategic recommendations

### Phase 4: Integration ✅
1. Create main workflow file ✅
2. Wire up all nodes in sequence ✅
3. Test end-to-end workflow execution ✅
4. Add error handling and logging ✅

**Implementation Notes:**
- Created `MonthlyActivitySummaryWorkflow` with proper node sequencing
- Implemented comprehensive response formatting with structured output
- Added detailed error handling and metadata tracking
- Created test event generation utility for validation
- Integrated proper workflow schema with node configurations

### Phase 5: Testing & Validation ✅
1. Create test data scenarios ✅
2. Validate SQL query results ✅
3. Test LLM summarization quality ✅
4. Performance testing ✅

**Implementation Notes:**
- Created comprehensive test script (`test_monthly_activity_summary.py`) with validation and full workflow testing
- Added workflow to `WorkflowRegistry` for proper system integration
- Implemented test event generation utility for easy testing
- Added detailed error handling and result validation
- Created structured output with JSON export for detailed analysis
- Test script includes both schema validation and end-to-end workflow testing

## ✅ WORKFLOW IMPLEMENTATION COMPLETED

### Summary of Completed Components:

1. **Schema Definition** (`app/schemas/monthly_activity_summary_schema.py`)
   - MonthlyActivitySummaryEvent with user_id, date range, and metadata validation

2. **SQL Templates** (`app/workflows/monthly_activity_summary_nodes/sql_templates.py`)
   - 4 comprehensive query templates for activity analysis
   - Proper joins between sf_activities, sf_contacts, and sf_users tables

3. **Workflow Nodes:**
   - `RequestCategoryNode` - Request classification (extensible for future types)
   - `SQLDataNode` - Database query execution with comprehensive error handling
   - `DataStructureNode` - Advanced data organization and analysis
   - `LLMSummaryNode` - OpenAI integration with structured output

4. **Main Workflow** (`app/workflows/monthly_activity_summary_workflow.py`)
   - Complete workflow orchestration
   - Comprehensive response formatting
   - Test event creation utilities

5. **Prompt Template** (`app/prompts/monthly_activity_summary/activity_summary.yaml`)
   - Specialized healthcare outreach analysis prompt
   - OpenAI GPT-4 configuration

6. **Testing & Validation** (`test_monthly_activity_summary.py`)
   - Complete test suite with validation scenarios
   - End-to-end workflow testing
   - Result export and analysis

### Ready for Production Use:
✅ All nodes implemented and integrated
✅ Error handling and logging throughout
✅ Comprehensive test suite created
✅ Workflow registered in system
✅ Documentation and architecture completed

## Technical Specifications

### Database Query Requirements
```sql
-- Core query structure (will be refined in implementation)
SELECT 
    a.description,
    a.activity_date,
    a.subject,
    c.name as contact_name,
    c.specialty,
    c.organization,
    u.name as user_name
FROM sf_activities a
JOIN sf_contacts c ON a.contact_id = c.id
JOIN sf_users u ON a.owner_id = u.salesforce_id
WHERE a.owner_id = ?
  AND a.activity_date >= ?
  AND a.activity_date <= ?
  AND a.description IS NOT NULL
ORDER BY a.activity_date DESC
```

### LLM Integration
- **Provider**: OpenAI
- **Model**: GPT-4 (configurable)
- **Temperature**: 0.7 (balanced creativity/accuracy)
- **Max Tokens**: 2000 (comprehensive summaries)

### Data Structure Format
```json
{
  "summary_period": {
    "start_date": "2024-01-01",
    "end_date": "2024-01-31"
  },
  "activities_by_specialty": {
    "Cardiology": [
      {
        "contact_name": "Dr. Smith",
        "activity_date": "2024-01-15",
        "key_discussion": "Discussed referral patterns..."
      }
    ]
  },
  "key_metrics": {
    "total_activities": 45,
    "unique_providers": 23,
    "specialties_covered": 8
  }
}
```

## Error Handling Strategy
- Database connection failures
- SQL query errors
- Data formatting issues
- LLM API failures
- Empty result sets

## Security Considerations
- Input validation for user_id and date parameters
- SQL injection prevention
- Rate limiting for LLM calls
- Sensitive data handling in logs

## Performance Targets
- Query execution: < 5 seconds
- Data structuring: < 2 seconds
- LLM processing: < 30 seconds
- Total workflow: < 45 seconds

## Future Enhancements (Post-MVP)
- Multiple report types (weekly, quarterly)
- Interactive report filtering
- Email delivery of summaries
- Comparative analysis (month-over-month)
- Export capabilities (PDF, Excel)
- Dashboard visualization integration 