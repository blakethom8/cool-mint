# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Claude.MD rules:
Standard Workflow
1. First think through the problem, read the codebase for relevant files, and write a plan to todo.md.
2. The plan should have a list of todo items that you can check off as you complete them
3. Before you begin working, check in with me and I will verify the plan.
4. Then, begin working on the todo items, marking them as complete as you go.
5. Please every step of the way just give me a high level explanation of what changes you made
6. Make every task and code change you do as simple as possible. We want to avoid making any massive or complex changes. Every change should impact as little code as possible. Everything is about simplicity.
7. Finally, add a review section to the todo.md file with a summary of the changes you made and any other relevant information.

## Project Overview

GenAI Launchpad is a production-ready framework for building scalable Generative AI applications using Python, FastAPI, and Docker. It provides an event-driven architecture with AI workflow support.

## Key Commands

### Development Environment

```bash
# From docker/ directory
./start.sh              # Start all services (PostgreSQL, Redis, Supabase, etc.)
./stop.sh              # Stop all services
./logs.sh              # View logs for all services

# Local development server (from app/ directory)
uvicorn main:app --host 0.0.0.0 --port 8080 --reload
```

### Database Operations

```bash
# From app/ directory
./makemigration.sh "description"  # Create new migration
./migrate.sh                      # Apply pending migrations
alembic upgrade head              # Apply all migrations
alembic downgrade -1              # Rollback one migration
```

### Code Quality

```bash
ruff check .          # Run linter
ruff format .         # Format code
```

### Workflow Creation

```bash
createworkflow        # Interactive workflow creation tool
```

## Architecture

### Event-Driven Workflow System

The core architecture revolves around workflows that process events through a series of nodes:

1. **Workflows** (`app/workflows/`): Define the processing pipeline
   - Inherit from `Workflow` base class
   - Define `workflow_schema` with nodes and connections
   - Example: `LangfuseTracingWorkflow`

2. **Nodes** (`app/workflows/*/nodes/`): Individual processing units
   - Inherit from `Node` base class
   - Implement `process()` method
   - Can be connected in sequence or parallel

3. **Events** (`app/schemas/`): Pydantic models defining input data
   - Inherit from `BaseEventSchema`
   - Define the data structure for workflow inputs

4. **Background Tasks** (`app/worker/`): Celery tasks for async processing
   - Handles long-running operations
   - Integrates with Redis for task queue

### Directory Structure

```
app/
├── api/            # FastAPI endpoints
├── core/           # Workflow engine core
├── database/       # SQLAlchemy models
├── prompts/        # AI prompt templates (YAML/Jinja2)
├── schemas/        # Pydantic models
├── services/       # Business logic
├── worker/         # Celery background tasks
└── workflows/      # Workflow definitions
```

### AI Integration

- **Multiple LLM Support**: OpenAI, Anthropic, Google Gemini, AWS Bedrock
- **Structured Output**: Uses `instructor` library for structured AI responses
- **Prompt Management**: YAML templates with Jinja2 support in `app/prompts/`
- **Observability**: Langfuse integration for LLM tracing

### External Services

- **Database**: PostgreSQL (via Supabase)
- **Cache/Queue**: Redis
- **Salesforce**: Integration via `simple-salesforce`
- **Web Scraping**: Firecrawl API integration

## Development Guidelines

### Creating a New Workflow

1. Use `createworkflow` command for scaffolding
2. Define event schema in `app/schemas/`
3. Create workflow nodes in `app/workflows/{workflow_name}_nodes/`
4. Define workflow in `app/workflows/{workflow_name}.py`
5. Register workflow in `app/workflows/workflow_registry.py`

### Database Changes

1. Make model changes in `app/database/models/`
2. Run `./makemigration.sh "description"` to create migration
3. Review generated migration in `app/alembic/versions/`
4. Apply with `./migrate.sh`

### Environment Variables

Key environment variables are loaded from `.env` files:
- `PROJECT_NAME`: Used for Docker network naming
- Database credentials
- API keys for various services
- See Docker compose files for full list

### Testing

Currently no formal testing framework is set up. Manual testing can be done in the `playground/` directory.

## Important Notes

- Python 3.12+ is required
- All services run in Docker containers
- Use absolute imports from `app` package
- Follow existing code patterns and conventions
- Langfuse tracing is integrated for AI observability
- Ruff is configured to exclude certain directories