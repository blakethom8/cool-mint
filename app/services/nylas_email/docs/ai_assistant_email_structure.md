# AI Assistant Email Processing Structure

## Use Case Overview
Users forward emails to `thomsonblakecrm@gmail.com` when they want their AI Assistant to take action. The AI needs to:
1. Parse the user's request
2. Extract context from the forwarded email
3. Identify required actions
4. Execute those actions

## Email Data Structure Analysis

### 1. **Forwarded Email Structure**
```
┌─────────────────────────────────────┐
│ User's Request to AI                │  <- What the user wants AI to do
├─────────────────────────────────────┤
│ Forwarded Message Divider           │  <- "---------- Forwarded message ---------"
├─────────────────────────────────────┤
│ Forwarded Email Metadata            │  <- Original sender, date, subject
├─────────────────────────────────────┤
│ Forwarded Email Content             │  <- The actual email thread
└─────────────────────────────────────┘
```

### 2. **Key Data Fields Available**

#### From Database (Email Table):
- **subject**: "Fwd: [Original Subject]"
- **from_email**: User who forwarded (e.g., "blakethomson8@gmail.com")
- **to_emails**: Always ["thomsonblakecrm@gmail.com"]
- **body**: Full HTML content including forwarded thread
- **snippet**: Preview text (first ~100 chars)
- **thread_id**: Unique to this forward (not original thread)
- **date**: When forwarded, not original email date

#### From Parsed Content:
- **User's Request**: Instructions before "Forwarded message"
- **Original Email Data**:
  - From, To, Date, Subject of original email
  - Full conversation thread if multiple replies
  - Attachments (if any)

### 3. **Example Data Structure for AI Processing**

```json
{
  "email_id": "7c1b11f8-0ed6-4bb0-94b1-a438fea2b973",
  "user_request": {
    "raw": "Could you log an MD-to-MD activity with Dr. McDonald and capture the notes from the thread?",
    "parsed_actions": [
      "log_md_to_md_activity",
      "capture_notes_from_thread"
    ]
  },
  "forwarded_email": {
    "from": "Blake Thomson <blakethomson8@gmail.com>",
    "to": "Devon McDonald <dvnmcdonald@gmail.com>",
    "subject": "Re: Ortho Lunch",
    "date": "Fri, Jul 25, 2025 at 2:22 PM"
  },
  "extracted_entities": {
    "people": [
      {"name": "Devon McDonald", "email": "dvnmcdonald@gmail.com", "role": "Physical Therapist"},
      {"name": "Dr. Uquillis", "organization": "Cedars", "role": "MD"}
    ],
    "organizations": ["Cedars"],
    "dates": ["Friday, July 25th", "60-days"]
  },
  "meeting_context": {
    "type": "MD-to-MD lunch",
    "topics": ["Patient sharing", "Epic integration"],
    "action_items": ["Work on Epic integration", "Follow up in 60 days"]
  }
}
```

## Common AI Action Types

Based on the lunch example, typical actions include:

### 1. **CRM Activities**
- Log meeting/call/email activity
- Update contact records
- Create follow-up tasks
- Add meeting notes

### 2. **Information Extraction**
- Meeting attendees and roles
- Key discussion points
- Action items and deadlines
- Contact information

### 3. **Workflow Triggers**
- Schedule follow-ups
- Create calendar events
- Send summary emails
- Update project status

## Processing Pipeline

```
1. Email Arrives → Webhook/Sync → Database
2. AI Triggered → Parse Request → Extract Context
3. Identify Actions → Execute Actions → Log Results
4. Send Confirmation → Update Email Status
```

## Key Considerations for AI Processing

### 1. **Request Parsing**
- User requests are often informal
- May contain multiple actions
- Need to infer context from email thread

### 2. **Entity Recognition**
- Names might appear differently (Dr. McDonald vs Devon McDonald)
- Email addresses are reliable identifiers
- Organizations may be mentioned indirectly

### 3. **Thread Context**
- Forwarded emails may contain entire threads
- Need to parse nested reply structure
- Chronological order may be reversed

### 4. **Action Mapping**
Examples:
- "log an activity" → Create CRM activity record
- "capture notes" → Extract and save meeting summary
- "schedule follow-up" → Create task with deadline
- "add to contacts" → Create/update contact record

## Next Steps for Implementation

1. **Create Email Classifier**
   - Identify forwarded emails requiring action
   - Categorize request types

2. **Build Request Parser**
   - Extract user instructions
   - Map to specific actions

3. **Implement Action Handlers**
   - CRM integration for logging activities
   - Task creation system
   - Contact management

4. **Design Feedback System**
   - Confirmation emails to user
   - Error handling and notifications
   - Action summaries