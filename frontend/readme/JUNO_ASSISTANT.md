# Juno Assistant - AI Email Processing System

## Overview

Juno Assistant is an AI-powered email processing system designed for physician liaison CRM workflows. It automatically analyzes incoming emails and suggests appropriate actions such as logging calls, adding notes, or setting reminders. The system uses a staging-to-persistent data transfer pattern that preserves AI predictions while allowing user corrections.

## Architecture

### Data Flow
1. **Email Ingestion**: Emails are synced from external sources into the system
2. **AI Processing**: Juno analyzes emails and creates suggested actions with staging data
3. **User Review**: Users review, edit, and approve actions through a modal interface
4. **Data Transfer**: Approved actions are transferred from staging tables to persistent tables
5. **Metrics Tracking**: Original AI predictions are preserved for accuracy analysis

### Key Design Decisions
- **Immutable Staging Data**: AI predictions are never modified, enabling long-term accuracy tracking
- **Delta Tracking**: System tracks differences between AI suggestions and user corrections
- **One-at-a-Time Processing**: Users must review each action individually to ensure quality

## API Endpoints

### Email Actions API (`/api/email-actions`)

#### List Email Actions
```
GET /api/email-actions
Query Parameters:
  - page: number (default: 1)
  - page_size: number (default: 20)  
  - status: string (pending, approved, rejected, completed, failed)
  - action_types: string[] (add_note, log_call, set_reminder)
  - user_email: string
  - start_date: string (ISO format)
  - end_date: string (ISO format)
  - search_text: string
  - sort_by: string (default: created_at)
  - sort_order: asc | desc (default: desc)

Response: EmailActionsListResponse
```

#### Get Dashboard Statistics
```
GET /api/email-actions/stats
Response: DashboardStatsResponse
```

#### Get Single Email Action
```
GET /api/email-actions/{action_id}
Response: EmailActionResponse
```

#### Update Email Action (Deprecated)
```
PATCH /api/email-actions/{action_id}
Body: EmailActionUpdateRequest
Note: This endpoint is deprecated. Use transfer endpoints instead.
```

#### Approve Action (Legacy)
```
POST /api/email-actions/{action_id}/approve
Response: ActionResultResponse
```

#### Reject Action
```
POST /api/email-actions/{action_id}/reject
Query Parameters:
  - reason: string (optional)
Response: ActionResultResponse
```

### Transfer API Endpoints

#### Transfer Call Log
```
POST /api/email-actions/call-logs/{staging_id}/transfer
Body: {
  user_id: string,
  final_values: {
    subject: string,
    description?: string,
    activity_date: string,
    duration_minutes?: number,
    mno_type: string,
    mno_subtype?: string,
    mno_setting: string,
    contact_ids: string[],
    primary_contact_id?: string
  }
}
Response: TransferResponse
```

#### Transfer Note
```
POST /api/email-actions/notes/{staging_id}/transfer
Body: {
  user_id: string,
  final_values: {
    note_content: string,
    note_type?: string,
    related_entity_type?: string,
    related_entity_id?: string,
    related_entity_name?: string
  }
}
Response: TransferResponse
```

#### Transfer Reminder
```
POST /api/email-actions/reminders/{staging_id}/transfer
Body: {
  user_id: string,
  final_values: {
    reminder_text: string,
    due_date: string,
    priority: 'high' | 'normal' | 'low',
    assignee?: string,
    assignee_id?: string,
    related_entity_type?: string,
    related_entity_id?: string,
    related_entity_name?: string
  }
}
Response: TransferResponse
```

### Emails API (`/api/emails`)

#### List Emails
```
GET /api/emails
Query Parameters: Similar to email actions
Response: EmailsListResponse
```

#### Sync Emails
```
POST /api/emails/sync
Response: { new_emails: number, message: string }
```

#### Process Emails
```
POST /api/emails/process
Body: { email_ids: string[] }
Response: ProcessResult[]
```

## Data Models

### Email Action
```typescript
interface EmailAction {
  id: string;
  email_id: string;
  action_type: 'add_note' | 'log_call' | 'set_reminder';
  action_parameters: Record<string, any>;
  confidence_score: number;
  reasoning: string;
  status: 'pending' | 'approved' | 'rejected' | 'completed' | 'failed';
  reviewed_at?: string;
  reviewed_by?: string;
  review_notes?: string;
  created_at: string;
  updated_at: string;
  email: EmailSummary;
  staging_data?: StagingData;
}
```

### Staging Data Types

#### Call Log Staging
```typescript
interface CallLogStaging {
  type: 'call_log';
  id: string;
  subject: string;
  description?: string;
  activity_date?: string;
  duration_minutes?: number;
  mno_type?: string;           // BD_Outreach, MD_to_MD_Visits, etc.
  mno_subtype?: string;
  mno_setting?: string;         // In-Person, Virtual, Phone, Email
  contact_ids?: string[];
  primary_contact_id?: string;
  approval_status: string;
  // Transfer tracking fields
  transferred_to_activity_id?: string;
  transfer_status?: string;
  transferred_at?: string;
  transfer_error?: string;
}
```

#### Note Staging
```typescript
interface NoteStaging {
  type: 'note';
  id: string;
  note_content: string;
  note_type?: string;
  related_entity_type?: string;
  related_entity_id?: string;
  related_entity_name?: string;
  approval_status: string;
  // Transfer tracking fields
  transferred_to_note_id?: string;
  transfer_status?: string;
  transferred_at?: string;
  transfer_error?: string;
}
```

#### Reminder Staging
```typescript
interface ReminderStaging {
  type: 'reminder';
  id: string;
  reminder_text: string;
  due_date: string;
  priority: 'high' | 'normal' | 'low';
  assignee?: string;
  assignee_id?: string;
  related_entity_type?: string;
  related_entity_id?: string;
  related_entity_name?: string;
  approval_status: string;
  // Transfer tracking fields
  transferred_to_reminder_id?: string;
  transfer_status?: string;
  transferred_at?: string;
  transfer_error?: string;
}
```

## User Experience

### Main Interface

The Juno Assistant interface consists of three main tabs:

1. **Emails Tab**
   - Lists all synced emails
   - Allows selection of multiple emails for processing
   - Sync button to fetch new emails
   - Process button to send selected emails to Juno

2. **Pending Actions Tab**
   - Shows all AI-suggested actions awaiting review
   - Badge indicates count of pending items
   - Click any action to open detail modal

3. **Completed Actions Tab**
   - Shows only Juno-assisted actions (with staging_data)
   - Excludes manually created actions
   - Provides audit trail of AI-assisted work

### Action Review Modal

The modal for reviewing actions is organized into three sections:

1. **Action Details (Top)**
   - Editable form fields specific to action type
   - All fields are directly editable (no edit mode)
   - Required fields marked with asterisks
   - For call logs:
     - Call Type dropdown (BD_Outreach, MD_to_MD_Visits, etc.)
     - Setting dropdown (In-Person, Virtual, Phone, Email)
     - Subject text field
     - Participants list with add/remove functionality
     - Primary contact selection
     - Description textarea
     - Activity date/time picker
     - Duration in minutes
     - Conditional subtype field

2. **Juno's Analysis (Middle)**
   - Confidence score percentage
   - AI reasoning explanation
   - Helps user understand AI's decision

3. **Email Context (Bottom)**
   - Original email metadata (From, Subject, Date)
   - User instructions if provided
   - Full email content

### Workflow Steps

1. **Email Processing**
   - User selects emails in Emails tab
   - Clicks "Process with Juno"
   - System queues emails for AI analysis
   - Automatically switches to Pending Actions tab

2. **Action Review**
   - User clicks pending action to open modal
   - Reviews AI suggestions
   - Edits fields as needed
   - Either:
     - Submits action (transfers to persistent storage)
     - Rejects action (with optional reason)

3. **Data Transfer**
   - Submit button validates required fields
   - Calls appropriate transfer API
   - Preserves original AI predictions
   - Tracks user modifications as delta

### Form Validation

Required fields by action type:

**Call Logs**:
- Call Type
- Setting
- Subject
- At least one participant
- Activity Date

**Notes**:
- Note Content

**Reminders**:
- Reminder Text
- Due Date

### Error Handling

- Form validation errors shown as list
- API errors displayed via notification system
- Loading states during async operations
- Confirmation dialogs for destructive actions

## Development Notes

### Key Frontend Services

1. **emailActionsService.ts**
   - Handles all email action API calls
   - Transfer methods for each staging type
   - Utility methods for formatting

2. **emailsApi.ts**
   - Email listing and syncing
   - Batch email processing

### State Management

The main JunoAssistant component manages global state:
```typescript
interface JunoAssistantState {
  actions: EmailAction[];
  selectedAction?: EmailAction;
  filters: EmailActionFilters;
  loading: boolean;
  error?: string;
  stats?: DashboardStats;
  activeTab: 'emails' | 'pending' | 'completed';
  page: number;
  pageSize: number;
  totalPages: number;
  sortBy: string;
  sortOrder: 'asc' | 'desc';
}
```

### Future Enhancements

1. **Bulk Operations**
   - Batch approval/rejection of actions
   - Bulk transfer API endpoints

2. **Advanced Filtering**
   - Filter by confidence score ranges
   - Filter by specific email addresses
   - Date range presets

3. **Analytics Dashboard**
   - AI accuracy metrics over time
   - User correction patterns
   - Action type distribution

4. **Integration Improvements**
   - Direct Salesforce contact lookup
   - Auto-complete for contact fields
   - Email thread detection

5. **User Authentication**
   - Replace hardcoded user ID with auth context
   - Role-based permissions
   - Audit logging with user attribution

## Testing Considerations

1. **API Mocking**
   - Mock transfer API responses
   - Test error scenarios
   - Validate form submissions

2. **UI Testing**
   - Modal interactions
   - Form validation
   - Tab switching
   - Pagination

3. **Data Integrity**
   - Verify staging data immutability
   - Test delta tracking accuracy
   - Validate transfer mappings

## Deployment Notes

- Environment variables needed:
  - API base URL
  - Authentication tokens
  - Feature flags

- Browser compatibility:
  - Modern browsers (Chrome, Firefox, Safari, Edge)
  - ES6+ JavaScript support required
  - CSS Grid and Flexbox support

- Performance considerations:
  - Pagination for large datasets
  - Lazy loading of email content
  - Debounced search inputs