# GenAI Project Launchpad

## Introduction

The GenAI Project Launchpad is a comprehensive, flexible, Docker-based framework designed to accelerate the development and deployment of production-ready Generative AI applications. It provides a solid foundation for building scalable, event-driven architectures with built-in AI pipeline support.

## Table of Contents

- [GenAI Project Launchpad](#genai-project-launchpad)
  - [Introduction](#introduction)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [Key Features](#key-features)
  - [Project Structure](#project-structure)
  - [Getting Started](#getting-started)
    - [Prerequisites](#prerequisites)
    - [Quick Start](#quick-start)
  - [Configuration](#configuration)
  - [Development Workflow](#development-workflow)
  - [Deployment](#deployment)
  - [Troubleshooting](#troubleshooting)
    - [Issues During Initial Deployment](#issues-during-initial-deployment)

## Overview

The GenAI Project Launchpad is not just another agent framework. It's a production-ready infrastructure with a modular architecture that combines various design patterns, frameworks, and technologies. This launchpad is tailored for developers who want to build and deploy quickly while maintaining full control over their codebase.

Key components include:

- FastAPI for efficient API development
- Celery for robust background task processing
- PostgreSQL for reliable data persistence
- Redis for high-performance task queue management
- Caddy for seamless reverse proxy and automatic HTTPS

All services are containerized using Docker, ensuring consistency across development and deployment environments.

## Key Features

- **Event-Driven Architecture**: Built-in support for designing and implementing event-driven systems.
- **AI Pipeline Support**: Pre-configured setup for integrating AI models and pipelines.
- **Scalability**: Designed with scalability in mind, allowing easy expansion as your application grows.
- **Flexibility**: Modular architecture that allows for easy customization and extension.
- **Production-Ready**: Includes essential components for a production environment, including logging, monitoring, and security features.
- **Rapid Development**: Boilerplate code and project structure to accelerate development.
- **Docker-Based Deployment**: Complete Docker-based strategy for straightforward deployment.

## Project Structure

```text
├── app
│   ├── alembic            # Database migration scripts
│   ├── api                # API endpoints and routers
│   ├── config             # Configuration files
│   ├── database           # Database models and utilities
│   ├── models             # Data models
│   ├── pipelines          # AI pipeline definitions
│   ├── prompts            # Prompt templates for AI models
│   ├── services           # Business logic and services
│   ├── tasks              # Background task definitions
│   └── utils              # Utility functions and helpers
├── docker                 # Docker configuration files
├── docs                   # Project documentation
├── playground             # Run experiments for pipeline design
└── requests               # Event definitions and handlers
```

## Getting Started

### Prerequisites

- Python 3
- Docker
- Git
- VS Code or Cursor (optional, but recommended)

### Quick Start

1. Clone the repository:

```bash
git clone https://github.com/datalumina/genai-project-launchpad.git
cd genai-project-launchpad
```

2. Set up environment files:

```bash
cp app/.env.example app/.env
cp docker/.env.example docker/.env
```

You can leave the `docker/.env` file as is for the quick start. However, you need to add your OpenAI API key to the `app/.env` file. Open `app/.env` and locate the `OPENAI_API_KEY` variable. Replace its value with your actual OpenAI API key:

```yaml
OPENAI_API_KEY=your_openai_api_key_here
```

3. Build and start the Docker containers:

```bash
cd ./docker
./start.sh
```

4. Make database migrations:

```bash
cd ../app
./makemigration.sh  # Create a new migration
./migrate.sh        # Apply migrations
```

When prompted for a migration message, you can enter a brief description like "Initial migration" or "Launch".

5. Start logging:

```bash
cd ../docker
./logs.sh
```

6. Populate the vector store:

To initialize the vector store with sample data, run:

```bash
python -m app.utils.insert_vectors
```

7. Send event:

Run the following command to send a test event using the invoice.json file and the request library:

```bash
python requests/send_event.py
```

You should get a `202` status code back and see the response logged in the terminal where you are running `./logs.sh`. Here you should see that the invoice service should be called and that the task is successfully completed.


This step creates necessary tables, indexes, and inserts initial vector data into the database.

8. Check database:

Connect to the database using your favorite database explorer. The default settings are:

- Host: localhost
- Port: 5432
- Database: launchpad
- Username: postgres
- Password: super-secret-postgres-password

In the `events` table, you should see the event you just processed. It contains the raw data (JSON) in the `data` column and the processed event (JSON) with in the `task_context` column.

9. Experiment in the playground:

The playground directory contains several Python scripts to help you experiment with different components of the GenAI Project Launchpad:

- Use `playground/models.py` to experiment with the LLM factory and structured output.
- Use `playground/pipeline.py` to run the pipeline with different example events.
- Use `playground/prompts.py` to test and refine prompt templates.

It is recommended to run these with the **Python interactive window**, which you can learn more about[here](https://youtu.be/mpk4Q5feWaw?t=1346). Also, make sure to create a new `venv` or `conda` environment and install the `requirements.txt`:

```bash
cd ./app
pip install -requirements.txt
```

If you're a VS Code or Cursor user, I also recommend adding the following settings to your `.code-workspace` file to help with imports and refactoring:

```json
"settings": {
  "jupyter.notebookFileRoot": "${workspaceFolder}/app",
  "python.analysis.extraPaths": ["./app"],
  "python.testing.pytestArgs": [
   "app"
  ],
}
```

For example, to experiment with the LLM factory and structured output:

```bash
python playground/models.py
```

To run the pipeline with a sample event:

```bash
python playground/pipeline.py
```

To test prompt templates:

```bash
python playground/prompts.py
```

Feel free to modify these scripts and use the example events in the `requests/events/` directory to better understand how the different components work together.

## Configuration

Configuration is managed through environment variables and settings files. Key configuration files:

- `app/.env`: Application-specific settings
- `docker/.env`: Docker and service configurations
- `app/config/settings.py`: Application-specific and LLM models

Refer to the `.env.example` files for available options.

## Development Workflow

Here's a high-level action plan to update the template for your unique project:

1. Update the '.env' files with your API keys and passwords
2. Update your settings in `app/config/settings.py`
3. Define the event(s) in `requests/events` (your incoming data)
4. Update the API schema in `app/api/schema/event.py` (matching your events)
5. Define your AI pipelines and processing steps in `app/pipelines/`
6. Define your result model in `app/models/domain/result.py`
7. Experiment with different AI models, data, and settings in the 'playground'
8. Fine-tune your pipelines and application flow


## Deployment

The project includes a complete Docker-based deployment strategy. To deploy:

1. Ensure your production configurations are set in the `.env` files.
2. Build and start the Docker containers:

```bash
cd docker
./start.sh
```

Caddy is pre-configured to handle HTTPS, simplifying the deployment process.

## Troubleshooting

### Issues During Initial Deployment

If you encounter any errors during the initial deployment, especially related to database connections or missing tables, it's recommended to remove all containers and volumes to start with a clean slate. This ensures that you're working with a fresh environment without any conflicting data from previous attempts.

Follow these steps to clean up your Docker environment:

1. Stop all running containers:

```bash
docker compose down
```

2. Remove all containers related to the project:

```bash
docker rm $(docker ps -a -q --filter name=launchpad_*)
```

3. Remove all volumes related to the project:

```bash
docker volume rm $(docker volume ls -q --filter name=launchpad_*)
```

4. Optionally, you can remove all unused volumes (be cautious if you have other projects using Docker):

```bash
docker volume prune
```

5. Rebuild and start the containers:

```bash
cd docker
./start.sh
```

6. Re-run the migration scripts:
 
```bash
cd ../app
./makemigration.sh
./migrate.sh
```

After performing these steps, you should have a clean environment to work with. If you continue to experience issues, please check the logs for more detailed error messages:

```bash
cd docker
./logs.sh
```

If problems persist, ensure that all environment variables are correctly set in your `.env` files and that there are no conflicts with other services running on your machine.

---

For further assistance or to contribute to the GenAI Project Launchpad, please consult the project maintainers or refer to the contribution guidelines.
