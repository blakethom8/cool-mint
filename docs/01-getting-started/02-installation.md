# Installation Guide

This guide walks you through setting up the GenAI Launchpad development environment.

## Prerequisites

Before you begin, ensure you have the following installed:

- Python 3.9 or higher
- Docker and Docker Compose
- Git
- A code editor (VS Code or Cursor recommended)

## Step-by-Step Installation

### 1. Clone the Repository

```bash
git clone -b boilerplate https://github.com/datalumina/genai-launchpad.git
cd genai-launchpad
```

### 2. Environment Setup

Create and configure the environment files:

```bash
cp app/.env.example app/.env
cp docker/.env.example docker/.env
```

Required environment variables:

```bash
# app/.env
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here  # Optional

# docker/.env
CADDY_DOMAIN=your_domain.com  # For production
```

### 3. Docker Environment

Navigate to the docker directory and start the containers:

```bash
cd docker
./start.sh
```

This command will:

- Build all required Docker images
- Start the services defined in docker-compose.yml
- Initialize the database
- Set up the Redis queue

### 4. Database Setup

Run the database migrations:

```bash
cd ../app
./makemigration.sh  # Create new migrations
./migrate.sh        # Apply migrations
```

### 5. Local Development Environment

Set up a Python virtual environment:

```bash
python -m venv venv

# Activate the virtual environment
# Windows:
venv\Scripts\activate
# Unix/macOS:
source venv/bin/activate

# Install dependencies
cd app
pip install -r requirements.txt
```

## Verifying the Installation

1. Check Services Status:
```bash
docker ps
```

Expected running containers:
- launchpad_api
- launchpad_database
- launchpad_redis
- launchpad_caddy

2. Test Database Connection:
```bash
psql -h localhost -p 5432 -U postgres -d launchpad
```

3. Verify API Access:
```bash
curl http://localhost:8000/health
```

## Common Installation Issues

### Database Connection Errors
- Ensure PostgreSQL container is running
- Check database credentials in .env file
- Verify port 5432 is not in use

### Docker Issues
- Run `docker compose down -v` to clean up
- Check Docker logs: `docker compose logs`
- Ensure ports 8000, 5432, and 6379 are available

### Python Environment Issues
- Verify Python version: `python --version`
- Ensure pip is updated: `pip install --upgrade pip`
- Check virtual environment activation

## Security Notes

- Never commit .env files
- Rotate API keys regularly
- Use strong database passwords
- Keep Docker and dependencies updated