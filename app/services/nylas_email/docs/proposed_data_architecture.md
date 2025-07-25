# Proposed Email Processing Data Architecture

## Core Design Principles
1. **Separation of Concerns**: Raw data → Parsed data → Actions → Logs
2. **Immutability**: Never modify raw data, always create new derived data
3. **Auditability**: Track every transformation and decision
4. **Flexibility**: Support multiple AI agents and workflows

## Database Schema Design

### 1. **emails** (Raw Data - Already Exists)
Keep this exactly as is - pure Nylas data
```sql
- id (UUID)
- nylas_id
- subject, body, from_email, to_emails, etc.
- raw_webhook_data (JSON)
- processed (boolean) - only flag, no modifications
```

### 2. **emails_parsed** (Structured Extraction)
```sql
CREATE TABLE emails_parsed (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email_id UUID REFERENCES emails(id),
    
    -- Parsing metadata
    parsed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    parser_version VARCHAR(50),
    
    -- Extracted request data
    is_forwarded BOOLEAN DEFAULT FALSE,
    user_request TEXT,  -- "log MD-to-MD activity..."
    request_intent VARCHAR(100),  -- 'activity_logging', 'scheduling', etc.
    
    -- Forwarded email metadata (if applicable)
    original_sender_email VARCHAR(255),
    original_sender_name VARCHAR(255),
    original_subject TEXT,
    original_date TIMESTAMP,
    
    -- Structured content
    extracted_entities JSONB,  -- {people: [], organizations: [], dates: []}
    meeting_details JSONB,     -- {type, attendees, topics, location}
    action_items JSONB,        -- [{item, deadline, assignee}]
    
    -- Content analysis
    sentiment VARCHAR(50),
    urgency_score INTEGER,
    requires_response BOOLEAN,
    
    -- Thread context
    thread_summary TEXT,
    previous_interactions INTEGER,
    
    INDEX idx_emails_parsed_email_id (email_id),
    INDEX idx_emails_parsed_intent (request_intent)
);
```

### 3. **email_classifications** (AI Decisions)
```sql
CREATE TABLE email_classifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email_id UUID REFERENCES emails(id),
    parsed_email_id UUID REFERENCES emails_parsed(id),
    
    -- Classification metadata
    classified_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    model_name VARCHAR(100),  -- 'gpt-4', 'claude-3', etc.
    model_version VARCHAR(50),
    confidence_score DECIMAL(3,2),
    
    -- Primary classification
    primary_category VARCHAR(100),  -- 'meeting_request', 'activity_log', etc.
    secondary_categories VARCHAR(100)[],
    
    -- Action routing
    recommended_workflow VARCHAR(100),  -- 'crm_activity_workflow', 'scheduling_workflow'
    required_actions JSONB,  -- [{action: 'create_activity', params: {...}}]
    
    -- Additional context
    classification_reasoning TEXT,
    extracted_parameters JSONB,
    
    INDEX idx_classifications_category (primary_category)
);
```

### 4. **agent_actions** (What AI Did)
```sql
CREATE TABLE agent_actions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email_id UUID REFERENCES emails(id),
    classification_id UUID REFERENCES email_classifications(id),
    
    -- Action metadata
    action_type VARCHAR(100),  -- 'create_crm_activity', 'schedule_meeting', etc.
    action_status VARCHAR(50),  -- 'pending', 'in_progress', 'completed', 'failed'
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Action details
    action_parameters JSONB,
    action_result JSONB,
    error_details JSONB,
    
    -- External references
    external_system VARCHAR(100),  -- 'salesforce', 'calendar', etc.
    external_id VARCHAR(255),  -- ID in external system
    
    -- Audit
    performed_by VARCHAR(100),  -- 'email_agent_v1'
    
    INDEX idx_agent_actions_status (action_status),
    INDEX idx_agent_actions_type (action_type)
);
```

### 5. **agent_logs** (Detailed Audit Trail)
```sql
CREATE TABLE agent_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email_id UUID REFERENCES emails(id),
    action_id UUID REFERENCES agent_actions(id),
    
    -- Log metadata
    logged_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    log_level VARCHAR(20),  -- 'info', 'warning', 'error'
    
    -- Log content
    stage VARCHAR(100),  -- 'parsing', 'classification', 'action_execution'
    message TEXT,
    details JSONB,
    
    -- Performance tracking
    duration_ms INTEGER,
    tokens_used INTEGER,
    
    INDEX idx_agent_logs_email_id (email_id),
    INDEX idx_agent_logs_stage (stage)
);
```

## Processing Pipeline

```
1. Raw Email Ingestion
   emails table → processed=false

2. Parsing Stage
   emails → emails_parsed
   - Extract user request
   - Parse forwarded content
   - Identify entities
   - Structure data for LLM

3. Classification Stage
   emails_parsed → email_classifications
   - Determine intent
   - Route to workflow
   - Extract parameters

4. Action Execution
   email_classifications → agent_actions
   - Execute workflow
   - Update external systems
   - Record results

5. Logging
   All stages → agent_logs
   - Audit trail
   - Error tracking
   - Performance metrics
```

## Workflow Examples

### Example 1: MD-to-MD Activity Logging
```json
// emails_parsed record
{
  "user_request": "log an MD-to-MD activity with Dr. McDonald",
  "request_intent": "activity_logging",
  "meeting_details": {
    "type": "MD-to-MD lunch",
    "attendees": [
      {"name": "Devon McDonald", "role": "Physical Therapist"}
    ],
    "topics": ["Epic integration", "Patient sharing"]
  }
}

// email_classifications record
{
  "primary_category": "crm_activity",
  "recommended_workflow": "create_crm_activity_workflow",
  "required_actions": [
    {
      "action": "create_activity",
      "params": {
        "type": "MD-to-MD Meeting",
        "contact": "Devon McDonald",
        "notes": "Discussed Epic integration..."
      }
    }
  ]
}

// agent_actions record
{
  "action_type": "create_crm_activity",
  "action_status": "completed",
  "external_system": "salesforce",
  "external_id": "ACT-12345"
}
```

## Benefits of This Architecture

1. **Clean Separation**: Raw emails never touched, all processing in separate tables
2. **Flexibility**: Can add new parsers, classifiers, or workflows without schema changes
3. **Debugging**: Complete audit trail from raw email to final action
4. **A/B Testing**: Can run multiple classifiers and compare results
5. **Reprocessing**: Can re-parse or re-classify emails with improved models
6. **Analytics**: Rich data for understanding email patterns and agent performance

## Implementation Strategy

### Phase 1: Foundation
1. Create emails_parsed table
2. Build parsing logic for forwarded emails
3. Store structured extractions

### Phase 2: Intelligence
1. Create email_classifications table
2. Integrate LLM for classification
3. Define workflow routing rules

### Phase 3: Actions
1. Create agent_actions and agent_logs tables
2. Build workflow executors
3. Integrate with external systems (CRM, calendar, etc.)

### Phase 4: Optimization
1. Add performance metrics
2. Build reprocessing capabilities
3. Create analytics dashboards

## Key Decisions to Make

1. **Parsing Strategy**: Rule-based vs. LLM-based extraction?
2. **Classification Model**: Which LLM? Fine-tuned or prompted?
3. **Workflow Engine**: Use existing (Celery) or build custom?
4. **External Integrations**: Which systems to connect first?
5. **Error Handling**: Retry logic, manual review queue?