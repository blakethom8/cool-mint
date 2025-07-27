# Email Actions Architecture

## Overview

The Email Actions system is an intelligent email processing workflow that automatically classifies and extracts actionable information from forwarded emails. Sales representatives can forward emails to the AI assistant (thomsonblakecrm@gmail.com) with instructions, and the system will prepare structured data for CRM actions.

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Data Flow](#data-flow)
3. [User Experience Examples](#user-experience-examples)
4. [Database Schema](#database-schema)
5. [Workflow Components](#workflow-components)
6. [Model Configuration](#model-configuration)
7. [Testing and Debugging](#testing-and-debugging)
8. [Future Enhancements](#future-enhancements)

## System Architecture

### High-Level Architecture

```
Sales Rep Email → AI Assistant Email → Nylas Webhook → Email Storage → EmailActionsWorkflow → Staging Tables → User Approval → Salesforce
```

### Key Components

1. **Email Ingestion (Nylas)**
   - Receives emails at thomsonblakecrm@gmail.com
   - Parses forwarded emails to extract user instructions
   - Stores enhanced email data with parsed fields

2. **EmailActionsWorkflow**
   - Node-based workflow for processing emails
   - Classifies intent and extracts action-specific data
   - Creates staging records for user approval

3. **Staging Tables**
   - Temporary storage for extracted data
   - Allows user review and modification
   - Tracks approval status

4. **Salesforce Integration**
   - Pushes approved actions to Salesforce
   - Creates activities, notes, and tasks

## Data Flow

### 1. Email Reception
```python
# Email arrives via Nylas webhook
Email → NylasEmailService → Email Table (with enhanced fields)
```

### 2. Workflow Processing
```python
# EmailActionsWorkflow processes the email
Email → IntentClassificationNode → ActionRouterNode → ExtractionNode → CreateStagingRecordNode
```

### 3. Data Storage
```python
# Creates records in staging tables
EmailAction (master record) → CallLogStaging/NoteStaging/ReminderStaging (detail records)
```

### 4. User Approval
```python
# User reviews and approves staged actions
Staging Record → User Review → Approval/Modification → Salesforce Push
```

## User Experience Examples

### Example 1: Logging an MD-to-MD Activity

**User Action:**
Sales rep forwards an email thread about a lunch meeting with instruction:
```
Chat, below is an email thread where we had MD-to-MD lunch with Devon McDonald who is a physical therapist. 
Please log an MD-to-MD activity with Dr. McDonald. We discussed the challenges with Epic integration and the 
patient that we share with Dr. Uquillis.
```

**System Response:**
1. Classifies as "log_call" action (confidence: 0.95)
2. Extracts:
   - Subject: "MD-to-MD Lunch with Devon McDonald"
   - Participants: Blake Thomson, Devon McDonald, Dr. Uquillis
   - Date: Extracted from email thread
   - Type: MD_to_MD_Visits
   - Key Topics: Epic integration challenges, patient sharing
3. Creates staging record for approval
4. User reviews and approves → Pushed to Salesforce as Task

### Example 2: Adding a Note

**User Action:**
Sales rep forwards product feedback email with instruction:
```
Add a note to Dr. Smith's account about their concerns with our new device sizing. 
They need smaller options for pediatric patients.
```

**System Response:**
1. Classifies as "add_note" action (confidence: 0.90)
2. Extracts:
   - Related Contact: Dr. Smith
   - Note Content: Concerns about device sizing, needs smaller pediatric options
   - Note Type: Product Feedback
3. Creates note staging record
4. User reviews, adds context → Pushed to Salesforce as Note

### Example 3: Setting a Reminder

**User Action:**
Sales rep sends direct email:
```
Remind me to follow up with the Cedar Sinai team in 60 days about their Epic integration progress.
```

**System Response:**
1. Classifies as "set_reminder" action (confidence: 0.95)
2. Extracts:
   - Reminder Text: Follow up on Epic integration progress
   - Due Date: 60 days from today
   - Related Entity: Cedar Sinai
   - Priority: Normal
3. Creates reminder staging record
4. User confirms date → Creates Salesforce Task with due date

### Example 4: Unknown/Multiple Actions

**User Action:**
Sales rep forwards complex email with multiple requests:
```
Please log this meeting, add notes about the budget discussion, and remind me to send the proposal next week.
```

**System Response:**
1. Classifies primary action as "log_call" (confidence: 0.70)
2. Notes additional actions detected
3. Creates primary staging record with note about additional requests
4. User can manually create additional actions

## Database Schema

### Core Tables

#### email_actions
```sql
CREATE TABLE email_actions (
    id UUID PRIMARY KEY,
    email_id UUID REFERENCES emails(id),
    action_type VARCHAR(50),  -- 'add_note', 'log_call', 'set_reminder'
    action_parameters JSONB,  -- Flexible parameters
    confidence_score FLOAT,
    reasoning TEXT,
    status VARCHAR(20),  -- 'pending', 'approved', 'rejected', 'completed'
    reviewed_at TIMESTAMP,
    reviewed_by VARCHAR(255),
    review_notes TEXT,
    executed_at TIMESTAMP,
    execution_result JSONB,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

#### call_logs_staging
```sql
CREATE TABLE call_logs_staging (
    id UUID PRIMARY KEY,
    email_action_id UUID REFERENCES email_actions(id),
    
    -- Activity fields (matching Salesforce structure)
    subject VARCHAR(255),
    description TEXT,
    activity_date TIMESTAMP,
    duration_minutes INTEGER,
    
    -- Classification fields
    mno_type VARCHAR(255),  -- 'MD_to_MD_Visits'
    mno_subtype VARCHAR(255),  -- 'MD_to_MD_w_Cedars'
    mno_setting VARCHAR(255),  -- 'In-Person', 'Virtual'
    
    -- Participants
    contact_ids JSONB,  -- Array of contact IDs/names
    primary_contact_id VARCHAR(255),
    
    -- Tracking fields
    suggested_values JSONB,  -- Original AI suggestions
    user_modifications JSONB,  -- User changes
    approval_status VARCHAR(20),
    approved_by VARCHAR(255),
    approved_at TIMESTAMP,
    
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

#### notes_staging
```sql
CREATE TABLE notes_staging (
    id UUID PRIMARY KEY,
    email_action_id UUID REFERENCES email_actions(id),
    
    -- Note fields
    note_content TEXT NOT NULL,
    note_type VARCHAR(50),  -- 'general', 'product_feedback', etc.
    
    -- Related entity
    related_entity_type VARCHAR(50),  -- 'contact', 'account'
    related_entity_id VARCHAR(255),
    related_entity_name VARCHAR(255),
    
    -- Tracking fields (same as above)
);
```

#### reminders_staging
```sql
CREATE TABLE reminders_staging (
    id UUID PRIMARY KEY,
    email_action_id UUID REFERENCES email_actions(id),
    
    -- Reminder fields
    reminder_text TEXT NOT NULL,
    due_date TIMESTAMP NOT NULL,
    priority VARCHAR(20),
    
    -- Assignment
    assignee VARCHAR(255),
    assignee_id VARCHAR(255),
    
    -- Related entity fields (same as notes)
    -- Tracking fields (same as above)
);
```

## Workflow Components

### 1. IntentClassificationNode
**Purpose:** Classifies email intent into action types

**Key Features:**
- Uses LLM to analyze email content and user instructions
- Returns action type with confidence score
- Provides reasoning for classification
- Extracts initial parameters

**Classification Logic:**
- Looks for keywords and patterns
- Considers context and user language
- Falls back to "unknown" for ambiguous requests

### 2. ActionRouterNode
**Purpose:** Routes to appropriate extraction node based on classification

**Routing Map:**
- `add_note` → AddNoteExtractionNode
- `log_call` → LogCallExtractionNode
- `set_reminder` → SetReminderExtractionNode
- `unknown` → UnknownActionNode

### 3. Extraction Nodes
**Purpose:** Extract action-specific parameters

**LogCallExtractionNode:**
- Extracts: subject, participants, date, duration, activity type
- Identifies MD-to-MD activities
- Captures discussion points and follow-ups

**AddNoteExtractionNode:**
- Extracts: note content, related entity, note type
- Identifies key topics and themes
- Links to contacts/accounts

**SetReminderExtractionNode:**
- Extracts: reminder text, due date, priority
- Calculates dates from relative references
- Identifies related entities

### 4. CreateStagingRecordNode
**Purpose:** Creates database records for extracted data

**Process:**
1. Creates EmailAction master record
2. Creates action-specific staging record
3. Stores original AI suggestions
4. Sets status to 'pending'

### 5. UnknownActionNode
**Purpose:** Handles unclassified or ambiguous requests

**Actions:**
- Logs the inability to classify
- Stores original request for manual review
- Suggests possible actions to user

## Model Configuration

### Workflow-Specific Configuration
```python
# app/.env
EMAIL_ACTIONS_CLASSIFICATION_PROVIDER=anthropic
EMAIL_ACTIONS_CLASSIFICATION_MODEL=claude-3-5-haiku-20241022
EMAIL_ACTIONS_EXTRACTION_PROVIDER=anthropic  
EMAIL_ACTIONS_EXTRACTION_MODEL=claude-3-5-sonnet-20241022
```

### Model Selection Strategy
- **Classification:** Fast, accurate model (Haiku)
- **Extraction:** More capable model for complex parsing (Sonnet)
- **Fallback:** OpenAI GPT-4 if Anthropic unavailable

## Testing and Debugging

### Test Script Usage
```bash
# List available emails
python workflows/email_actions/test_email_actions.py --list

# Test specific email
python workflows/email_actions/test_email_actions.py <email_id>

# Test most recent email
python workflows/email_actions/test_email_actions.py
```

### Common Issues and Solutions

1. **Classification Errors**
   - Check user instruction clarity
   - Review confidence thresholds
   - Analyze reasoning output

2. **Extraction Failures**
   - Verify email content structure
   - Check for missing required fields
   - Review model prompts

3. **Database Errors**
   - Ensure migrations are applied
   - Check field type compatibility
   - Verify foreign key relationships

### Debugging Tips
- Enable Langfuse tracing for LLM calls
- Check workflow logs for node execution
- Review staging table contents
- Examine EmailAction reasoning field

## Future Enhancements

### 1. Multi-Action Support
- Process multiple actions from single email
- Create action chains and dependencies
- Batch approval interface

### 2. Smart Entity Resolution
- Automatic contact/account matching
- Fuzzy name matching with suggestions
- Integration with Salesforce search

### 3. Learning and Improvement
- Track approval/rejection patterns
- Fine-tune classification based on feedback
- Personalize to user preferences

### 4. Advanced Features
- Email thread analysis
- Attachment processing
- Calendar integration for meetings
- Automated follow-up scheduling

### 5. Integration Enhancements
- Real-time Salesforce validation
- Duplicate detection
- Conflict resolution
- Bulk action processing

## Security and Compliance

### Data Privacy
- Email content encrypted at rest
- PII handling in staging tables
- Audit trail for all actions

### Access Control
- Role-based approval permissions
- Delegation for team coverage
- Activity logging

### Compliance
- HIPAA considerations for medical data
- Data retention policies
- Right to deletion support

## Performance Considerations

### Optimization Strategies
- Async processing via Celery
- Batch database operations
- Caching for entity lookups
- Rate limiting for LLM calls

### Monitoring
- Workflow execution times
- Classification accuracy metrics
- User approval rates
- Error tracking and alerts

## Conclusion

The Email Actions system provides an intelligent, flexible solution for converting email communications into structured CRM actions. By combining advanced NLP with a staging/approval workflow, it maintains data quality while saving time for sales representatives.

The architecture supports future expansion while maintaining simplicity for the core use cases of logging activities, adding notes, and setting reminders.