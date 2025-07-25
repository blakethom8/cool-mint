# Email Services Architecture Documentation

## Overview

This document describes the architecture of the email processing system built using Nylas, Pinggy, and an agentic workflow framework. The system is designed to receive emails via webhooks, classify them, and execute appropriate actions based on the email content.

## Architecture Components

### 1. External Services

#### Nylas API
- **Purpose**: Email integration platform providing unified API access to email accounts
- **Key Features**:
  - OAuth authentication for Gmail/email accounts
  - Webhook notifications for real-time email events
  - Email sending, attachment handling, and folder management
- **Configuration**: Requires API key, client ID, and grant ID stored in environment variables

#### Pinggy Tunnel
- **Purpose**: Secure tunnel service exposing local development server to the internet
- **Key Features**:
  - No account required
  - HTTPS endpoints for webhook reception
  - Simple SSH-based setup: `ssh -p 443 -R0:localhost:8000 free.pinggy.io`
- **Flow**: Internet → Pinggy → Local Server (port 8000)

### 2. Core Services

#### FastAPI Application (Port 8080)
- **Main Entry Point**: `/` endpoint receives Nylas webhooks
- **Responsibilities**:
  - Validates incoming webhook events
  - Persists events to PostgreSQL database
  - Queues tasks to Celery for async processing
  - Returns 202 Accepted response immediately

#### Celery Worker
- **Task Queue**: Redis-based task queue
- **Main Task**: `process_incoming_event`
- **Workflow Execution**: Processes emails through the agentic workflow system
- **Auto-reload**: Uses watchdog for development hot-reloading

### 3. Email Processing Workflow

#### Classification Node
- **Purpose**: Categorizes incoming emails using GPT-4o-mini
- **Categories**:
  - `spam`: Unwanted promotional emails
  - `invoice`: Financial/billing communications
  - `general`: General business communications
  - `genai_accelerator`: Course-related emails
  - `other`: Legitimate emails not fitting above categories

#### Router Node
- **Purpose**: Routes emails to appropriate handler based on classification
- **Handlers**:
  - `HandleSpamNode`: Manages spam emails
  - `ProcessInvoiceNode`: Processes financial documents
  - `SendMessageNode`: Handles general communications
  - `HandleGenAIAcceleratorNode`: Manages course-related queries

#### Nylas Service (`nylas_service.py`)
- **Email Operations**:
  - `send_email()`: Send new emails or replies
  - `download_attachment()`: Retrieve email attachments
  - `delete_email()`: Remove emails
  - `add_email_to_folder()`: Organize emails into folders

### 4. Infrastructure

#### Docker Services
```yaml
api:
  - FastAPI application
  - Port: 8080
  - Auto-runs Alembic migrations
  - Hot-reload enabled

celery_worker:
  - Async task processor
  - Watches for code changes
  - Single worker concurrency

redis:
  - Task queue broker
  - Port: 6379
  - Health checks enabled

db:
  - Supabase PostgreSQL
  - Port: 5432
  - Persistent volume storage
```

#### Network Architecture
```
                    ┌─────────────┐
                    │   Nylas     │
                    │   Webhooks  │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   Pinggy    │
                    │   Tunnel    │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  FastAPI    │
                    │  Port 8080  │
                    └──────┬──────┘
                           │
                ┌──────────┴──────────┐
                │                     │
         ┌──────▼──────┐      ┌──────▼──────┐
         │ PostgreSQL  │      │    Redis    │
         │  Database   │      │    Queue    │
         └─────────────┘      └──────┬──────┘
                                     │
                              ┌──────▼──────┐
                              │   Celery    │
                              │   Worker    │
                              └──────┬──────┘
                                     │
                              ┌──────▼──────┐
                              │  Workflow   │
                              │   Engine    │
                              └─────────────┘
```

## Setup Process

### 1. Nylas Configuration
1. Create Nylas developer account
2. Set up OAuth callback: `http://localhost:5010/oauth/exchange`
3. Authenticate Gmail account
4. Store grant ID in `.env`

### 2. Webhook Setup
1. Start Pinggy tunnel: `ssh -p 443 -R0:localhost:8000 free.pinggy.io`
2. Add Pinggy URL to `.env` as `SERVER_URL`
3. Run webhook configuration script
4. Store webhook secret in `.env`

### 3. Docker Deployment
```bash
# Start all services
docker-compose up -d

# Services will be available at:
# - API: http://localhost:8080
# - Redis: localhost:6379
# - PostgreSQL: localhost:5432
```

## Environment Variables

```env
# Nylas Configuration
NYLAS_CLIENT_ID=your_client_id
NYLAS_API_KEY=your_api_key
NYLAS_API_URI=https://api.us.nylas.com
NYLAS_GRANT_ID=your_grant_id
EMAIL=your_email@domain.com

# Webhook Configuration
SERVER_URL=https://your-pinggy-url
WEBHOOK_SECRET=your_webhook_secret

# Database Configuration
POSTGRES_HOST=db
POSTGRES_DB=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_PORT=5432

# AI Model Keys
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
# ... other AI keys
```

## Key Features for Migration

1. **Webhook-Based Architecture**: Real-time email processing without polling
2. **Agentic Workflow System**: Modular node-based processing pipeline
3. **Multi-Model AI Support**: Configurable AI providers for classification
4. **Async Processing**: Non-blocking API with background task execution
5. **Development-Friendly**: Hot-reload, local tunneling, and Docker containerization

## Security Considerations

- Webhook signatures validated using WEBHOOK_SECRET
- Database credentials isolated in environment variables
- Redis and PostgreSQL not exposed to public network
- Pinggy provides HTTPS encryption for webhook traffic

This architecture provides a robust foundation for email processing with easy extensibility through the node-based workflow system.