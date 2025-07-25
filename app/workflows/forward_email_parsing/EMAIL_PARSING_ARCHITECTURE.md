# Email Parsing Architecture

## Overview

This document outlines the architecture for parsing and extracting structured data from emails, particularly focusing on forwarded emails where users request AI assistance. The system uses a node-based workflow architecture to process emails through multiple stages of extraction and analysis.

## Core Design Principles

1. **Separation of Concerns**: Raw email data remains untouched; all parsing creates new derived data
2. **Workflow-Based Processing**: Uses existing node architecture for modular, testable components
3. **LLM-Powered Extraction**: Leverages language models for intelligent data extraction
4. **Confidence Scoring**: Tracks extraction confidence for quality assurance
5. **Iterative Refinement**: Designed to support continuous improvement of extraction algorithms

## Database Schema

### emails_parsed Table

```sql
CREATE TABLE emails_parsed (
    -- Primary Keys
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email_id UUID REFERENCES emails(id) UNIQUE NOT NULL,
    
    -- Parsing Metadata
    parsed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    parser_version VARCHAR(50) DEFAULT 'v1.0',
    model_used VARCHAR(100),  -- 'gpt-4', 'claude-3', etc.
    
    -- Email Classification
    is_forwarded BOOLEAN DEFAULT FALSE,
    is_action_required BOOLEAN DEFAULT FALSE,
    email_type VARCHAR(100),  -- 'forwarded_request', 'direct_email', 'auto_reply'
    
    -- User Request (for forwarded emails)
    user_request TEXT,  -- Raw request: "log MD-to-MD activity..."
    request_intents JSONB,  -- ["log_activity", "capture_notes"]
    
    -- Forwarded Email Metadata
    forwarded_from JSONB,  -- {email, name, date, subject}
    forwarded_thread_id VARCHAR(255),  -- Original thread ID if extractable
    
    -- Extracted Entities
    people JSONB,  -- [{name, email, role, organization, confidence}]
    organizations JSONB,  -- [{name, type, confidence}]
    dates_mentioned JSONB,  -- [{date, context, type: 'meeting'/'deadline'}]
    locations JSONB,  -- [{place, address, type}]
    
    -- Structured Content
    meeting_info JSONB,  -- {type, attendees, date, topics, location}
    action_items JSONB,  -- [{task, deadline, assignee, priority}]
    key_topics JSONB,  -- ["Epic integration", "Patient sharing"]
    
    -- Thread Context
    thread_summary TEXT,
    thread_participants JSONB,  -- All unique participants in thread
    thread_message_count INTEGER,
    
    -- Sentiment & Priority
    sentiment VARCHAR(50),  -- 'positive', 'neutral', 'negative'
    urgency_score INTEGER CHECK (urgency_score >= 0 AND urgency_score <= 10),
    
    -- Name Resolution (for CRM matching)
    entity_mappings JSONB,  -- {"Dr. McDonald": "devon_mcdonald_123"}
    
    -- Indexes
    INDEX idx_parsed_email_id (email_id),
    INDEX idx_parsed_type (email_type),
    INDEX idx_parsed_action_required (is_action_required),
    INDEX idx_parsed_urgency (urgency_score DESC)
);
```

## Workflow Architecture

### Email Parsing Workflow Structure

```python
class EmailParsingWorkflow(Workflow):
    workflow_schema = WorkflowSchema(
        description="Parse and extract structured data from emails",
        event_schema=EmailParsingEventSchema,
        start=EmailTypeDetectionNode,
        nodes=[
            NodeConfig(
                node=EmailTypeDetectionNode,
                connections=[ForwardedEmailExtractionNode, DirectEmailExtractionNode],
                is_router=True,
                description="Detect if email is forwarded with request"
            ),
            NodeConfig(
                node=ForwardedEmailExtractionNode,
                connections=[EntityExtractionNode],
                description="Extract user request and forwarded content"
            ),
            NodeConfig(
                node=DirectEmailExtractionNode,
                connections=[EntityExtractionNode],
                description="Process direct emails"
            ),
            NodeConfig(
                node=EntityExtractionNode,
                connections=[MeetingDetailsExtractionNode],
                description="Extract people, orgs, dates"
            ),
            NodeConfig(
                node=MeetingDetailsExtractionNode,
                connections=[ActionItemExtractionNode],
                description="Extract meeting-specific information"
            ),
            NodeConfig(
                node=ActionItemExtractionNode,
                connections=[EntityResolutionNode],
                description="Extract action items and tasks"
            ),
            NodeConfig(
                node=EntityResolutionNode,
                connections=[SaveParsedEmailNode],
                description="Map entities to CRM records"
            ),
            NodeConfig(
                node=SaveParsedEmailNode,
                connections=[],
                description="Save to emails_parsed table"
            )
        ]
    )
```

### Node Descriptions

#### 1. EmailTypeDetectionNode (Router)
- **Purpose**: Determines email type and routes to appropriate extraction path
- **Output**: Email classification (forwarded_request, direct_email, auto_reply)
- **Routing Logic**: Routes to ForwardedEmailExtractionNode if forwarded with request

#### 2. ForwardedEmailExtractionNode
- **Purpose**: Extracts user request and separates forwarded content
- **Key Extractions**:
  - User's request/instructions
  - Intent classification (log_activity, schedule_meeting, etc.)
  - Original email metadata
  - Forwarded email body

#### 3. DirectEmailExtractionNode
- **Purpose**: Handles non-forwarded emails
- **Key Extractions**:
  - Direct request or information
  - Email intent and purpose

#### 4. EntityExtractionNode
- **Purpose**: Uses LLM to extract all entities with context
- **Extractions**:
  - People (name, email, role, organization)
  - Organizations
  - Dates and times
  - Locations
  - Each with confidence scores

#### 5. MeetingDetailsExtractionNode
- **Purpose**: Specialized extraction for meeting-related content
- **Extractions**:
  - Meeting type
  - Attendees
  - Topics discussed
  - Meeting outcomes

#### 6. ActionItemExtractionNode
- **Purpose**: Identifies tasks and action items
- **Extractions**:
  - Task descriptions
  - Deadlines
  - Assignees
  - Priority levels

#### 7. EntityResolutionNode
- **Purpose**: Maps extracted entities to existing CRM records
- **Functions**:
  - Name matching (Dr. McDonald → Devon McDonald)
  - Organization matching
  - Contact lookup

#### 8. SaveParsedEmailNode
- **Purpose**: Persists all extracted data to emails_parsed table
- **Functions**:
  - Data validation
  - Database insertion
  - Error handling

## LLM Extraction Strategy

### Multi-Stage Approach
1. **Fast Classification**: Quick email type detection
2. **Structural Extraction**: Separate user request from content
3. **Deep Extraction**: Detailed entity and context extraction
4. **Specialized Extraction**: Domain-specific extractions (meetings, tasks)
5. **Resolution**: Match to existing data

### Prompt Engineering
- Structured output using Pydantic models
- Few-shot examples for consistency
- Chain-of-thought for complex reasoning
- Confidence scoring for uncertain extractions

### Example Prompts

```python
# Email Type Detection
system_prompt = """
You are an email classifier. Determine if an email is:
1. A forwarded email with a user request for AI assistance
2. A direct email
3. An auto-reply or system message

Look for forwarding indicators and user instructions.
"""

# Entity Extraction
system_prompt = """
Extract all people, organizations, dates, and locations from the email.
For each entity, provide:
- Full name/title
- Any associated email addresses
- Role or position
- Organization affiliation
- Confidence score (0-1)

Consider context and relationships between entities.
"""
```

## Implementation Phases

### Phase 1: Basic Infrastructure (Current)
- [x] Create directory structure
- [x] Write architecture documentation
- [ ] Create emails_parsed table migration
- [ ] Implement EmailParsingEventSchema
- [ ] Create base workflow structure

### Phase 2: Core Extraction
- [ ] EmailTypeDetectionNode
- [ ] ForwardedEmailExtractionNode
- [ ] Basic EntityExtractionNode
- [ ] SaveParsedEmailNode
- [ ] End-to-end testing

### Phase 3: Advanced Extraction
- [ ] MeetingDetailsExtractionNode
- [ ] ActionItemExtractionNode
- [ ] Enhanced entity extraction
- [ ] Confidence scoring

### Phase 4: Integration
- [ ] EntityResolutionNode with CRM lookup
- [ ] Workflow triggering from parsed data
- [ ] Performance optimization
- [ ] Production deployment

## Example Data Flow

### Input: Forwarded Email
```
Subject: Fwd: Ortho Lunch
From: blakethomson8@gmail.com
To: thomsonblakecrm@gmail.com

Chat, below is an email thread where we had MD-to-MD lunch with Devon McDonald who is a physical therapist. We identified that she does share her patients with us but we need to work on our Epic integration.

Could you log an MD-to-MD activity with Dr. McDonald and capture the notes from the thread?

---------- Forwarded message ---------
From: Blake Thomson <blakethomson8@gmail.com>
Date: Fri, Jul 25, 2025 at 2:22 PM
Subject: Re: Ortho Lunch
To: Devon McDonald <dvnmcdonald@gmail.com>

Hi Devon,
Thanks for taking the time to meet with us! ...
```

### Output: Parsed Data
```json
{
  "email_type": "forwarded_request",
  "is_action_required": true,
  "user_request": "log an MD-to-MD activity with Dr. McDonald and capture the notes from the thread",
  "request_intents": ["log_activity", "capture_notes"],
  "people": [
    {
      "name": "Devon McDonald",
      "email": "dvnmcdonald@gmail.com",
      "role": "Physical Therapist",
      "confidence": 0.95
    },
    {
      "name": "Blake Thomson",
      "email": "blakethomson8@gmail.com",
      "role": "MD",
      "confidence": 0.9
    }
  ],
  "meeting_info": {
    "type": "MD-to-MD lunch",
    "date": "2025-07-25",
    "attendees": ["Devon McDonald", "Blake Thomson", "Dr. Uquillis"],
    "topics": ["Patient sharing", "Epic integration"],
    "location": null
  },
  "action_items": [
    {
      "task": "Work on Epic integration",
      "assignee": "internal_team",
      "priority": "high"
    },
    {
      "task": "Follow up in 60 days",
      "deadline": "2025-09-23",
      "assignee": "Blake Thomson"
    }
  ],
  "key_topics": ["Epic integration", "Patient sharing", "Physical therapy collaboration"],
  "sentiment": "positive",
  "urgency_score": 3
}
```

## Testing Strategy

### Unit Tests
- Individual node testing with mock data
- LLM prompt testing with examples
- Database operations

### Integration Tests
- Full workflow execution
- Multiple email types
- Error handling scenarios

### Test Data Categories
1. Forwarded emails with clear requests
2. Complex email threads
3. Direct emails
4. Edge cases (no clear request, multiple requests)

## Monitoring and Metrics

### Key Metrics
- Extraction accuracy by field
- Processing time per email
- LLM token usage
- Confidence score distribution
- Error rates by node

### Quality Assurance
- Manual review queue for low-confidence extractions
- A/B testing new extraction models
- Feedback loop for continuous improvement

## Security Considerations

- No PII in logs
- Encrypted storage for sensitive data
- Access control for parsed data
- Audit trail for all extractions

## Future Enhancements

1. **Multi-language Support**: Extract from non-English emails
2. **Attachment Processing**: Extract data from PDFs, images
3. **Smart Routing**: Auto-trigger appropriate workflows
4. **Learning System**: Improve extraction based on corrections
5. **Real-time Processing**: Stream processing for immediate action