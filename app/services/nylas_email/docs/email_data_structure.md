# Email Data Structure Guide

## Overview
Our email system bridges Nylas's email API with our local PostgreSQL database, creating a structured way to store, process, and act on emails.

## Data Flow
```
Nylas API → Webhook/Sync → Our Database → AI Processing → Actions
```

## Database Schema

### 1. Email Table (Main Entity)
The core table that stores all email messages:

#### Nylas Identifiers
- **nylas_id**: Unique ID from Nylas (e.g., "19843664e0a2764a")
- **grant_id**: The Nylas grant representing the email account
- **thread_id**: Groups related emails together (conversations)

#### Email Metadata
- **subject**: Email subject line
- **snippet**: Preview text (first ~100 chars of body)
- **date**: Unix timestamp when email was sent
- **received_at**: When we received it in our system

#### Participants
- **from_email**: Sender's email address
- **from_name**: Sender's display name
- **to_emails**: JSON array of recipient emails
- **cc_emails**: JSON array of CC recipients
- **bcc_emails**: JSON array of BCC recipients

#### Content
- **body**: Full HTML email body
- **body_plain**: Plain text version (if available)

#### Status Flags
- **unread**: Whether email is unread (from Nylas)
- **starred**: Whether email is starred (from Nylas)
- **processed**: Whether our AI has processed it
- **processing_status**: Current processing state
- **classification**: AI-assigned category

#### Additional Metadata
- **folders**: JSON array of folder IDs
- **labels**: JSON array of label IDs
- **has_attachments**: Boolean flag
- **attachments_count**: Number of attachments
- **raw_webhook_data**: Complete Nylas webhook payload

### 2. EmailAttachment Table
Stores metadata about file attachments:

- **email_id**: Foreign key to Email
- **nylas_id**: Nylas attachment ID
- **filename**: Original filename
- **content_type**: MIME type (e.g., "application/pdf")
- **size**: File size in bytes
- **content_id**: For inline images
- **is_inline**: Whether embedded in email body
- **storage_path**: Local storage location (if downloaded)
- **downloaded**: Whether we've downloaded the file

### 3. EmailActivity Table
Tracks actions taken on emails:

- **email_id**: Foreign key to Email
- **activity_type**: Type of action (replied, forwarded, archived)
- **activity_data**: JSON with action-specific details
- **performed_by**: Who/what performed the action
- **performed_at**: When action occurred

## Nylas Message Object Structure

Here's what Nylas sends us:

```python
{
    "id": "19843664e0a2764a",
    "grant_id": "your-grant-id",
    "thread_id": "19843664e0a2764a",
    "subject": "Test # 233",
    "from": [{
        "email": "blakethomson8@gmail.com",
        "name": "Blake Thomson"
    }],
    "to": [{
        "email": "thomsonblakecrm@gmail.com",
        "name": ""
    }],
    "cc": [],
    "bcc": [],
    "date": 1737834223,  # Unix timestamp
    "unread": true,
    "starred": false,
    "snippet": "Test email to see what happens !",
    "body": "<html>Full HTML content...</html>",
    "attachments": [{
        "id": "attachment-id",
        "filename": "document.pdf",
        "content_type": "application/pdf",
        "size": 1024000
    }],
    "folders": ["INBOX"],
    "labels": []
}
```

## Key Design Decisions

### 1. **Separate Processing Layer**
- Emails are stored first, processed later
- Allows for retry logic and different processing strategies
- `processed` flag tracks completion

### 2. **JSON Storage for Lists**
- `to_emails`, `cc_emails`, `folders`, `labels` stored as JSON
- Flexible for varying email structures
- PostgreSQL JSON queries available if needed

### 3. **Activity Tracking**
- Separate table for audit trail
- Can track multiple actions per email
- Extensible for future action types

### 4. **Attachment Handling**
- Metadata stored immediately
- Actual files downloaded on-demand
- Preserves Nylas IDs for retrieval

### 5. **Raw Data Preservation**
- `raw_webhook_data` stores complete Nylas payload
- Useful for debugging and future migrations
- Can reprocess if schema changes

## Processing Workflow

1. **Ingestion**: Email arrives via webhook or sync
2. **Storage**: Basic data extracted and stored
3. **Classification**: AI analyzes and categorizes
4. **Action**: Based on classification, trigger workflows
5. **Tracking**: Record all actions in EmailActivity

## Use Cases for AI Processing

With this structure, you can:

1. **Smart Inbox**: Classify emails (invoices, support, spam)
2. **Auto-Reply**: Generate context-aware responses
3. **Data Extraction**: Pull structured data from emails
4. **Task Creation**: Convert emails to tasks/tickets
5. **Attachment Processing**: Analyze PDFs, images
6. **Conversation Threading**: Understand email context
7. **Sentiment Analysis**: Gauge customer satisfaction
8. **Priority Routing**: Send urgent emails to right person

## Query Examples

```sql
-- Get unprocessed emails
SELECT * FROM emails 
WHERE processed = false 
ORDER BY date DESC;

-- Find emails with attachments
SELECT e.*, COUNT(a.id) as attachment_count
FROM emails e
JOIN email_attachments a ON e.id = a.email_id
GROUP BY e.id;

-- Track email activities
SELECT e.subject, a.activity_type, a.performed_at
FROM emails e
JOIN email_activities a ON e.id = a.email_id
ORDER BY a.performed_at DESC;
```

## Next Steps for AI Integration

1. **Workflow Triggers**: Define what triggers processing
2. **Classification Rules**: What categories to use
3. **Action Mappings**: What to do for each category
4. **Response Templates**: For auto-replies
5. **Integration Points**: CRM, ticketing systems, etc.