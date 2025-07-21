# Activity Bundling & LLM Integration System

## Overview

This system allows users to select activities from a table, bundle them together with metadata, and then interact with Large Language Models (LLMs) to analyze and generate insights from the selected activities. The architecture is designed for scalability and provides a seamless user experience from activity selection to AI-powered analysis.

## System Architecture

### High-Level Flow
1. **Activity Selection** → User browses and filters activities, selecting relevant ones
2. **Bundle Creation** → Selected activities are packaged into a named bundle with statistics
3. **Bundle Management** → Users can view, manage, and select from saved bundles
4. **LLM Interaction** → Chat interface for querying selected activity bundles
5. **Response Management** → Save and organize important LLM responses

### Technology Stack

#### Backend (FastAPI + PostgreSQL)
- **Framework**: FastAPI with SQLAlchemy ORM
- **Database**: PostgreSQL with Alembic migrations
- **LLM Integration**: Anthropic Claude API (Claude 3.5 Sonnet) with comprehensive conversation management
- **Architecture**: Event-driven workflow system with REST APIs

#### Frontend (React + TypeScript)
- **Framework**: React 18 with TypeScript
- **Routing**: React Router v7
- **Styling**: CSS Modules with custom components
- **HTTP Client**: Axios for API communication
- **Build Tool**: Vite

## Backend Architecture

### Database Schema

#### Core Tables
```sql
-- Activity bundles - Collections of selected activities
activity_bundles:
  - id (UUID, primary key)
  - name (String, required) 
  - description (Text, optional)
  - activity_ids (Array of Strings) -- Salesforce activity IDs
  - activity_count (Integer)
  - token_count (Integer) -- Estimated tokens for LLM processing
  - created_by (String) -- User identifier
  - created_at, updated_at (DateTime)

-- LLM conversation sessions
llm_conversations:
  - id (UUID, primary key)
  - bundle_id (UUID, foreign key to activity_bundles)
  - model (String) -- e.g., "claude-3-5-sonnet-20241022"
  - messages (JSONB) -- Array of conversation messages
  - total_tokens_used (Integer)
  - created_at, updated_at (DateTime)

-- Saved LLM responses for future reference
saved_llm_responses:
  - id (UUID, primary key)
  - conversation_id (UUID, foreign key to llm_conversations)
  - prompt (Text)
  - response (Text)
  - note (Text, optional) -- User note about why saved
  - metadata (JSONB) -- Tags, categories, etc.
  - saved_at (DateTime)
```

### API Endpoints

#### Activity & Bundle Management
```
POST /api/activities/selection/stats    # Get bundle statistics preview
POST /api/activities/selection          # Create bundle from selected activities

GET  /api/bundles                      # List all bundles with pagination
GET  /api/bundles/{bundle_id}          # Get bundle details with activities
DELETE /api/bundles/{bundle_id}        # Delete bundle and conversations
```

#### LLM Integration
```
POST /api/llm/conversations                    # Create new conversation
GET  /api/llm/conversations                    # List conversations
GET  /api/llm/conversations/{conversation_id}  # Get conversation details
POST /api/llm/conversations/{id}/messages      # Send message to LLM

POST /api/llm/responses/save                   # Save specific response
GET  /api/llm/responses/saved                  # List saved responses
```

### Key Backend Files

#### Models & Database
- `app/database/data_models/activity_bundles.py` - SQLAlchemy models for bundles, conversations, responses
- `app/alembic/versions/7d1b772a8951_*.py` - Database migration for new tables
- `app/database/data_models/salesforce_data.py` - Existing activity data models

#### API Endpoints
- `app/api/activities.py` - Enhanced with bundle creation endpoints
- `app/api/bundles.py` - Bundle CRUD operations
- `app/api/llm.py` - LLM conversation management
- `app/api/router.py` - Main API router configuration

#### Schemas & Validation
- `app/schemas/bundle_schema.py` - Pydantic models for bundle operations
- `app/schemas/llm_schema.py` - Pydantic models for LLM interactions
- `app/schemas/activity_api_schema.py` - Enhanced with bundle fields

## Frontend Architecture

### Component Structure

#### Core Components
```
src/
├── App.tsx                 # Main router with ActivitySelector and Bundle Management
├── components/
│   ├── ActivityTable.tsx   # Enhanced table with selection tracking
│   ├── ActivityFilters.tsx # Collapsible filtering sidebar
│   ├── BundleCreationModal.tsx # Modal for creating bundles
│   ├── BundleList.tsx      # Bundle list with search, sort, pagination
│   ├── BundleDetail.tsx    # Bundle preview with activity details
│   └── LLMChat.tsx         # Full chat interface with Claude integration
├── pages/
│   └── BundleManagement.tsx # Two-column bundle management page
├── services/
│   ├── activityService.ts  # Original activity API calls
│   ├── bundleService.ts    # Bundle management API calls
│   └── llmService.ts       # Claude LLM interaction API calls
└── types/
    ├── activity.ts         # Activity type definitions
    ├── bundle.ts          # Bundle type definitions
    └── llm.ts             # LLM conversation type definitions
```

#### Routing Structure
```
/ (root)           → ActivitySelector page (activity table with filters)
/bundles           → Bundle Management page (fully implemented)
/bundles/{id}      → Bundle Management with specific bundle selected
```

### Key Frontend Files

#### Main Application
- `src/App.tsx` - Router setup and main ActivitySelector component
- `src/main.tsx` - React application entry point

#### Activity Management
- `src/components/ActivityTable.tsx` - Enhanced table with selection tracking and pagination
- `src/components/ActivityFilters.tsx` - Collapsible sidebar with comprehensive filtering
- `src/components/ActivityTable.css` - Optimized table styling with improved column widths

#### Bundle Creation
- `src/components/BundleCreationModal.tsx` - Modal showing statistics and creation form
- `src/components/BundleCreationModal.css` - Modal styling with responsive design
- `src/services/bundleService.ts` - API service for bundle operations

#### Bundle Management & LLM Integration
- `src/pages/BundleManagement.tsx` - Two-column layout with bundle list and chat interface
- `src/components/BundleList.tsx` - Search, sort, pagination for bundle selection
- `src/components/BundleDetail.tsx` - Rich bundle preview with expandable activities
- `src/components/LLMChat.tsx` - Full chat interface with Claude integration
- `src/services/llmService.ts` - Complete Anthropic Claude API service
- `src/types/bundle.ts` - Bundle-related TypeScript interfaces
- `src/types/llm.ts` - LLM conversation TypeScript interfaces

## User Experience Flow

### 1. Activity Selection
- Users browse activities in an optimized table with 6 columns:
  - Date, Subject (with specialties), Owner, Type, Contacts, Description
- Collapsible filter sidebar with search, date range, and category filters
- Multi-select with visual selection count and "Process Selected Activities" button

### 2. Bundle Creation
- Click "Process Selected Activities" opens modal with:
  - Bundle statistics: activity count, estimated tokens, unique owners, date range
  - Activity type breakdown
  - Name and description fields
- Real-time token estimation using tiktoken for accurate LLM cost estimation

### 3. Bundle Management (Implemented)
- Redirect to `/bundles` page after creation
- Two-column responsive layout:
  - Left: Bundle list with search, sort, pagination, and deletion
  - Right: Bundle detail view or LLM chat interface
- Bundle selection loads conversation history
- Smooth transitions between bundle details and active conversations

### 4. LLM Interaction with Claude (Implemented)
- Full chat interface with Claude 3.5 Sonnet integration
- Rich activity context automatically included in first message
- Real-time conversation with message history and timestamps
- Token usage tracking and cost monitoring
- Response saving with notes and metadata
- Suggested prompts for healthcare activity analysis
- Copy message functionality and response export options

## Token Management & Cost Optimization

### Token Counting Strategy
- **Creation Time**: Estimate tokens during bundle creation using tiktoken
- **Runtime**: Track actual tokens used during LLM conversations
- **Context Optimization**: Include activity context only in first user message
- **Fallback**: Character-based estimation if tiktoken fails (1 token ≈ 4 characters)

### Context Preparation
Activities leverage rich structured data from the existing `llm_context_json` field:
```json
{
  "basic_info": {
    "activity_id": "00TUJ0000156HSs2AM",
    "date": "2024-09-19",
    "subject": "Meeting w/ Inspire Sleep",
    "description": "Lunch Meeting w/ Cassidy Preston - Inspire",
    "owner": "Sara Murphy",
    "type": "Other",
    "subtype": "Other"
  },
  "structured_context": {
    "contacts": [
      {
        "contact_name": "William A Li",
        "specialty": "Neurology", 
        "organization": "William Li |",
        "is_physician": true,
        "mn_primary_geography": "Core"
      }
    ],
    "status": "Completed",
    "priority": "High",
    "activity_date": "2024-09-19"
  }
}
```

## Configuration & Environment

### Backend Environment Variables
```bash
ANTHROPIC_API_KEY=your_anthropic_api_key
DATABASE_URL=postgresql://...
```

### Frontend Configuration
```typescript
// API base URL in services
const API_BASE_URL = 'http://localhost:8080/api';
```

## Development Workflow

### Running the System
```bash
# Backend (from app/ directory)
uvicorn main:app --host 0.0.0.0 --port 8080 --reload

# Frontend (from frontend/ directory)
npm run dev
```

### Database Migrations
```bash
# Create migration
./makemigration.sh "description"

# Apply migrations
./migrate.sh
```

## API Documentation

### Bundle Creation Response Example
```json
{
  "selected_count": 25,
  "activity_ids": ["00TUJ0000156HSs2AM", "..."],
  "estimated_tokens": 3750,
  "bundle_id": "123e4567-e89b-12d3-a456-426614174000",
  "message": "Activities selected successfully. Ready for LLM processing."
}
```

### LLM Message Response Example
```json
{
  "message": "Based on the activities, the key success metrics are...",
  "tokens_used": 892,
  "total_tokens": 2847
}
```

## Recent Implementation (July 2025)

### Completed Bundle Management System
✅ **Complete two-column bundle management interface**
✅ **Anthropic Claude 3.5 Sonnet integration** 
✅ **Rich healthcare activity analysis** using structured data
✅ **Real-time conversation management** with message history
✅ **Token tracking and cost optimization**
✅ **Response saving and export functionality**

### Key Features Delivered
1. ✅ **BundleList Component** - Search, sort, pagination, and bundle deletion
2. ✅ **LLMChat Interface** - Full conversation with Claude API integration  
3. ✅ **Response Management** - Save responses with notes and metadata
4. ✅ **Structured Data Integration** - Rich context from existing `llm_context_json`
5. ✅ **Healthcare Intelligence** - Business insights, referral patterns, network analysis

### Future Enhancement Opportunities
- **Advanced Analytics Dashboard** - Aggregate insights across multiple bundles
- **Prompt Template Library** - Expandable collection of healthcare-specific prompts
- **Batch Processing** - Analyze multiple bundles simultaneously
- **Export Enhancements** - PDF reports and advanced formatting options
- **Integration Expansions** - Additional LLM providers and specialized models

## Security Considerations

- **API Keys**: Server-side only, never exposed to frontend
- **Input Sanitization**: All user inputs validated with Pydantic
- **Rate Limiting**: Consider implementing for LLM endpoints
- **Cost Monitoring**: Token tracking prevents runaway costs
- **Error Handling**: Comprehensive error handling throughout the stack

## Performance Optimizations

- **Database Indexing**: Comprehensive indexes on bundle and conversation tables
- **Token Estimation**: Efficient tiktoken usage with fallback mechanisms
- **Pagination**: All list endpoints support pagination
- **Lazy Loading**: Conversation messages loaded on-demand
- **Caching**: Consider Redis for frequently accessed bundles

This system provides a solid foundation for activity analysis with LLMs while maintaining scalability, user experience, and cost control.