# Quick start

The quick start assumes you have already completed all the installation steps from the previous chapter.

#### Populate the vector store

To initialize the vector store with sample data, run:

```bash
python app/utils/insert_vectors.py
```

#### Send event

Run the following command to send a test event using the invoice.json file and the request library:

```bash
python requests/send_event.py
```

You should get a `202` status code back and see the response logged in the terminal where you are running `./logs.sh`.
Here you should see that the invoice service should be called and that the task is successfully completed.

#### Check database

Connect to the database using your favorite database explorer. The default settings are:

- Host: localhost
- Port: 5432
- Database: launchpad
- Username: postgres
- Password: super-secret-postgres-password

In the `events` table, you should see the event you just processed. It contains the raw data (JSON) in the `data` column
and the processed event (JSON) with in the `task_context` column.

#### Experiment in the playground

The playground directory contains several Python scripts to help you experiment with different components of the GenAI
Launchpad:

- Use `playground/llm_playground.py` to experiment with the LLM factory and structured output.
- Use `playground/pipeline_playground.py` to run the pipeline with different example events.
- Use `playground/prompt_playground.py` to test and refine prompt templates.

It is recommended to run these with the **Python interactive window**, which you can learn more
about [here](https://youtu.be/mpk4Q5feWaw?t=1346).

If you're a VS Code or Cursor user, I also recommend adding the following settings to your `.code-workspace` file to
help with imports and refactoring:

```json
{
  "settings": {
    "jupyter.notebookFileRoot": "${workspaceFolder}/app",
    "python.analysis.extraPaths": [
      "./app"
    ],
    "python.testing.pytestArgs": [
      "app"
    ]
  }
}
```

For example, to experiment with the LLM factory and structured output:

```bash
python playground/llm_playground.py
```

To run the pipeline with a sample event:

```bash
python playground/pipeline_playground.py
```

To test prompt templates:

```bash
python playground/prompt_playground.py
```

Feel free to modify these scripts and use the example events in the `requests/events/` directory to better understand
how the different components work together.

## Configuration

Configuration is managed through environment variables and settings files. Key configuration files:

- `app/.env`: Application-specific settings
- `docker/.env`: Docker and service configurations
- `app/config/settings.py`: Application-specific and LLM models

Refer to the `.env.example` files for available options.

## Development Workflow

Here's a high-level action plan to update the template for your unique project:

1. Update the '.env' files with your API keys and passwords
2. Update your settings in `app/config`
3. Define the event(s) in `requests/events` (your incoming data)
4. Update the API schema in `app/api/event_schema.py` (matching your events)
5. Define your AI pipelines and processing steps in `app/pipelines/`
6. Add your vector embeddings to the database using `app/utils/insert_vectors.py` (optional, for RAG)
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

If you encounter any errors during the initial deployment, especially related to database connections or missing tables,
it's recommended to remove all containers and volumes to start with a clean slate. This ensures that you're working with
a fresh environment without any conflicting data from previous attempts.

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

After performing these steps, you should have a clean environment to work with. If you continue to experience issues,
please check the logs for more detailed error messages:

```bash
cd docker
./logs.sh
```

If problems persist, ensure that all environment variables are correctly set in your `.env` files and that there are no
conflicts with other services running on your machine.
