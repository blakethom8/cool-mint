---
id: linux-mac
sidebar_position: 2
---

# Linux & macOS

## Prerequisites

Before you begin, ensure you have the following installed:

- Python 3.12.x
- Docker and Docker Compose
- Git

### 1. Clone the repository

Open your Git Bash or Ubuntu WSL terminal and navigate to the desired path where you want to clone the launchpad code.

```bash
cd desired/project/path
```

Clone the repository.

```bash
git clone git@github.com:datalumina/genai-launchpad.git
```

### 2. Set .env files

Cd into the genai-launchpad directory.

```bash
cd genai-launchpad
```

Copy the .env.example files in both the `app/` and `docker/` directories

```bash
cp app/.env.example app/.env && cp docker/.env.example docker/.env
```

### 3. Building and starting the Docker containers

Navigate to the `docker/` directory and start the containers.

```bash
cd docker && ./start.sh
```

This command will:

- Build all Docker containers
- Start all Docker containers via docker compose

Run the following command to verify that all the Docker containers are running.

```bash
docker ps
```

Expected running containers:

- launchpad_celery_worker
- launchpad_api
- launchpad_redis
- launchpad_database
- launchpad_caddy

### 4. Database migrations

Create and apply database migrations using Alembic:

Cd into the `app/` directory

```bash
cd ../app
```

Run the `makemigration.sh` script, this will prompt for a message to describe the migration. Here you can enter
something like: 'init db'.

```bash
./makemigration.sh
```

Run the `migrate.sh` script, this will apply the migration that we just created.

```bash
./migrate.sh
```

### 5. Local development environment

Set up a Python virtual environment:

Create the virtual environment.

```bash
cd ../ && python -m venv venv
```

Activate the virtual environment.

```bash
source ./venv/bin/activate
```

Install dependencies.

```bash
pip install -r app/requirements.txt
```
