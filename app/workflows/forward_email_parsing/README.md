# Forward Email Parsing Workflow

## Overview

The Forward Email Parsing Workflow is an AI-powered system that processes emails (especially forwarded emails) to extract structured data, identify user requests, and prepare the data for downstream actions. It uses a node-based architecture with configurable AI models.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Setup Instructions](#setup-instructions)
3. [Workflow Nodes](#workflow-nodes)
4. [Running the Workflow](#running-the-workflow)
5. [Model Configuration](#model-configuration)
6. [Database Schema](#database-schema)
7. [Testing](#testing)
8. [Troubleshooting](#troubleshooting)

## Architecture Overview

```
Email Input → Type Detection → Content Extraction → Entity Extraction → 
→ Meeting Details → Action Items → Entity Resolution → Save to Database
```

The workflow uses AI models to intelligently parse emails and extract:
- User requests and intents
- People, organizations, dates, and locations
- Meeting information
- Action items and tasks
- Email classification and urgency

## Setup Instructions

### 1. Environment Variables

Add these to your `.env` file:

```bash
# Email Parsing Workflow Model Configuration
EMAIL_PARSING_MODEL_PROVIDER=anthropic  # Options: openai, anthropic, gemini, bedrock
EMAIL_PARSING_DEFAULT_MODEL=claude-3-5-sonnet-20241022
EMAIL_PARSING_FAST_MODEL=claude-3-5-haiku-20241022

# API Keys (based on provider choice)
ANTHROPIC_API_KEY=your-key-here
OPENAI_API_KEY=your-key-here  # If using OpenAI
GEMINI_API_KEY=your-key-here   # If using Gemini

# Nylas Configuration (for email access)
NYLAS_API_KEY=your-nylas-key
NYLAS_GRANT_ID=your-grant-id
```

### 2. Database Setup

The workflow requires the `emails_parsed` table. If not already created:

```bash
# From the app directory
./migrate.sh
```

### 3. Dependencies

Ensure all dependencies are installed:

```bash
uv sync
```

## Workflow Nodes

### 1. EmailTypeDetectionNode (Router)

**Purpose**: Determines if an email is a forwarded request, direct email, or auto-reply.

**Key Features**:
- Uses fast AI model for quick classification
- Routes to appropriate extraction path
- Provides confidence scores

**Output**:
```python
{
    "email_type": "forwarded_request",
    "is_forwarded": true,
    "has_user_request": true,
    "confidence": 0.95,
    "reasoning": "Email contains forwarding indicators..."
}
```

### 2. ForwardedEmailExtractionNode

**Purpose**: Extracts user requests and forwarded content from forwarded emails.

**Extracts**:
- User's request/instructions (e.g., "log an MD-to-MD activity")
- Request intents (e.g., ["log_activity", "capture_notes"])
- Original email metadata
- Forwarded email content

**Example User Requests**:
- "Could you log an MD-to-MD activity with Dr. McDonald"
- "Please schedule a follow-up meeting based on this thread"
- "Extract the action items from this conversation"

### 3. DirectEmailExtractionNode

**Purpose**: Processes non-forwarded emails.

**Extracts**:
- Email purpose
- Whether action is required
- Key topics discussed

### 4. EntityExtractionNode

**Purpose**: Extracts all entities mentioned in the email.

**Entities Extracted**:
```python
{
    "people": [
        {
            "name": "Devon McDonald",
            "email": "dvnmcdonald@gmail.com",
            "role": "Physical Therapist",
            "organization": "Red Iron Physical Therapy",
            "confidence": 0.95
        }
    ],
    "organizations": [
        {
            "name": "Cedars-Sinai",
            "type": "Hospital",
            "confidence": 0.9
        }
    ],
    "dates": [
        {
            "date": "2025-07-25",
            "context": "MD-to-MD lunch meeting",
            "type": "meeting"
        }
    ],
    "locations": [
        {
            "place": "Conference Room B",
            "type": "meeting_room"
        }
    ]
}
```

### 5. MeetingDetailsExtractionNode

**Purpose**: Extracts meeting-specific information if applicable.

**Extracts**:
- Meeting type (lunch, call, in-person)
- Attendees and their roles
- Meeting date/time
- Topics discussed
- Location

### 6. ActionItemExtractionNode

**Purpose**: Identifies tasks and action items.

**Extracts**:
```python
{
    "action_items": [
        {
            "task": "Work on Epic integration",
            "deadline": null,
            "assignee": "internal_team",
            "priority": "high"
        },
        {
            "task": "Follow up with Devon in 60 days",
            "deadline": "2025-09-23",
            "assignee": "Blake Thomson",
            "priority": "medium"
        }
    ]
}
```

### 7. EntityResolutionNode

**Purpose**: Maps extracted entities to existing CRM records.

**Current Implementation**: Creates placeholder mappings. In production, this would:
- Query your CRM for matching contacts
- Resolve name variations (Dr. McDonald → Devon McDonald)
- Link to existing records

### 8. SaveParsedEmailNode

**Purpose**: Saves all extracted data to the `emails_parsed` table.

**Features**:
- Consolidates data from all nodes
- Calculates urgency scores
- Handles duplicate detection
- Provides success/error status

## Running the Workflow

### Method 1: Using the Test Script

The test script provides several options for testing email parsing:

#### List Available Emails
```bash
python workflows/forward_email_parsing/test_email_parsing.py --list
```

This shows all emails in your database with their IDs, subjects, and senders.

#### Parse a Specific Email by ID
```bash
python workflows/forward_email_parsing/test_email_parsing.py c41e6992-9c49-4d20-a6cf-e2e7e3fd5436
```

Replace the UUID with any email ID from your database.

#### Run Default Test (Most Recent Forwarded Email)
```bash
python workflows/forward_email_parsing/test_email_parsing.py
```

This automatically finds and parses the most recent forwarded email and a direct email.

### Method 2: Process Email Programmatically

Create a script or use Python shell:

```python
from workflows.forward_email_parsing_workflow import ForwardEmailParsingWorkflow
from schemas.email_parsing_schema import EmailParsingEventSchema
from database.session import db_session
from database.data_models.email_data import Email

# Get email from database
for session in db_session():
    email = session.query(Email).filter_by(id="your-email-uuid").first()
    
    if email:
        # Create event data
        event_data = {
            "email_id": email.id,
            "subject": email.subject,
            "from_email": email.from_email,
            "from_name": email.from_name,
            "to_emails": email.to_emails or [],
            "body": email.body,
            "body_plain": email.body_plain,
            "snippet": email.snippet,
            "date": email.date,
            "thread_id": email.thread_id,
            "nylas_id": email.nylas_id,
            "force_reparse": True  # Set to True to reprocess
        }
        
        # Run workflow
        workflow = ForwardEmailParsingWorkflow()
        result = workflow.run(event_data)
        
        print(f"Workflow completed. Parsed email ID: {result.nodes.get('SaveParsedEmailNode', {}).get('parsed_email_id')}")
    break
```

### Method 3: Integration with Email Sync

In your email processing pipeline:

```python
from workflows.workflow_registry import WorkflowRegistry

# After syncing email from Nylas
workflow = WorkflowRegistry.FORWARD_EMAIL_PARSING.value()
result = workflow.run(email_event_data)
```

### Method 4: Check Parsed Results

View parsed emails in the database:

```bash
python workflows/forward_email_parsing/check_parsed_emails.py
```

## Model Configuration

### Workflow-Specific Model Settings

The workflow uses its own model configuration via environment variables:

```bash
# Provider choice
EMAIL_PARSING_MODEL_PROVIDER=anthropic

# Model selection
EMAIL_PARSING_DEFAULT_MODEL=claude-3-5-sonnet-20241022  # For extraction tasks
EMAIL_PARSING_FAST_MODEL=claude-3-5-haiku-20241022      # For classification
```

### Supported Providers and Models

#### Anthropic (Recommended)
```bash
EMAIL_PARSING_MODEL_PROVIDER=anthropic
EMAIL_PARSING_DEFAULT_MODEL=claude-3-5-sonnet-20241022
EMAIL_PARSING_FAST_MODEL=claude-3-5-haiku-20241022
```

#### OpenAI
```bash
EMAIL_PARSING_MODEL_PROVIDER=openai
EMAIL_PARSING_DEFAULT_MODEL=gpt-4
EMAIL_PARSING_FAST_MODEL=gpt-3.5-turbo
```

#### Google Gemini
```bash
EMAIL_PARSING_MODEL_PROVIDER=gemini
EMAIL_PARSING_DEFAULT_MODEL=gemini-pro
EMAIL_PARSING_FAST_MODEL=gemini-flash
```

#### AWS Bedrock
```bash
EMAIL_PARSING_MODEL_PROVIDER=bedrock
EMAIL_PARSING_DEFAULT_MODEL=anthropic.claude-v2
EMAIL_PARSING_FAST_MODEL=anthropic.claude-instant-v1
```

### Changing Models at Runtime

You can temporarily override models:

```python
import os

# Override for this session
os.environ["EMAIL_PARSING_MODEL_PROVIDER"] = "openai"
os.environ["EMAIL_PARSING_DEFAULT_MODEL"] = "gpt-4"

# Then run workflow
workflow = ForwardEmailParsingWorkflow()
```

## Database Schema

The workflow creates records in the `emails_parsed` table:

```sql
emails_parsed
├── id (UUID)
├── email_id (UUID) - References original email
├── parsed_at (timestamp)
├── parser_version
├── model_used
├── email_type (forwarded_request, direct_email, auto_reply)
├── is_forwarded (boolean)
├── is_action_required (boolean)
├── user_request (text)
├── request_intents (JSONB array)
├── people (JSONB array)
├── organizations (JSONB array)
├── meeting_info (JSONB)
├── action_items (JSONB array)
├── urgency_score (0-10)
└── entity_mappings (JSONB)
```

## Testing

### 1. Test Model Configuration

Check which models are being used:

```bash
python workflows/forward_email_parsing/test_model_config.py
```

### 2. Test Email Parsing

Process emails with various options:

```bash
# List all available emails
python workflows/forward_email_parsing/test_email_parsing.py --list

# Parse a specific email by ID
python workflows/forward_email_parsing/test_email_parsing.py <email-id>

# Run default test on most recent emails
python workflows/forward_email_parsing/test_email_parsing.py
```

### 3. Test Specific Email Types

The test script processes both:
- Forwarded emails with user requests
- Direct emails

## Troubleshooting

### Common Issues

#### 1. API Key Errors
```
Error: Set the `ANTHROPIC_API_KEY` environment variable
```
**Solution**: Ensure your API key is in `.env` and loaded properly.

#### 2. Model Not Found
```
Error: Model 'claude-3-5-sonnet' not found
```
**Solution**: Use the full model name with date: `claude-3-5-sonnet-20241022`

#### 3. Database Connection
```
Error: emails_parsed table not found
```
**Solution**: Run migrations: `./migrate.sh`

#### 4. Import Errors
```
ModuleNotFoundError: No module named 'pydantic_ai'
```
**Solution**: Run `uv sync` to install dependencies

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Then run workflow
workflow = ForwardEmailParsingWorkflow()
```

### Performance Tips

1. **Use fast models for classification**: The EmailTypeDetectionNode uses the fast model by default
2. **Batch processing**: Process multiple emails in parallel using Celery
3. **Caching**: The workflow avoids reprocessing emails unless `force_reparse=True`

## Example Use Cases

### 1. CRM Activity Logging
User forwards a meeting email with: "Log this MD-to-MD activity"
- Extracts meeting participants
- Identifies discussion topics
- Creates activity record

### 2. Task Creation
User forwards email with: "Create follow-up tasks from this thread"
- Extracts action items
- Assigns deadlines
- Creates tasks in project management system

### 3. Meeting Scheduling
User forwards email with: "Schedule a follow-up based on this"
- Extracts participant availability
- Identifies meeting topics
- Proposes meeting times

### 4. Email Summarization
User forwards long thread with: "Summarize this conversation"
- Extracts key points
- Identifies decisions made
- Creates concise summary

## Next Steps

1. **Integrate with Action Workflows**: Build workflows that act on parsed data
2. **Connect to External Systems**: CRM, calendar, task management
3. **Add Custom Extractors**: Industry-specific entity extraction
4. **Implement Feedback Loop**: Learn from user corrections

## Support

For issues or questions:
1. Check the logs in `docker logs cool-mint_celery_worker`
2. Review parsed data with `check_parsed_emails.py`
3. Verify model configuration with `test_model_config.py`