# Project Specification: Scalable Web Crawling & Validation Pipeline

## 1. Objective

This document outlines the architecture and implementation plan for building a scalable, multi-stage pipeline to discover, extract, and validate information from websites. The goal is to leverage our existing event-driven and asynchronous framework to process a large number of URLs in parallel, ensuring the final data is clean, validated, and stored reliably.

## 2. Core Architectural Concepts

This project is built on the core principles of our application's architecture:

*   **Event-Driven:** Every step in the pipeline is an "event." An event is created and stored in our `events` database table, providing a persistent, auditable record of every job in the system.
*   **Asynchronous Processing:** All heavy lifting is performed by background Celery workers. This keeps our API responsive and allows us to process tasks that take seconds or even minutes without blocking the system.
*   **Chained Workflows (Node Transfer):** Our system uses a generic dispatcher pattern. Instead of creating many different Celery tasks, we have one generic task (`process_incoming_event`) that reads a `workflow_type` from an event. Workflows themselves are "nodes" in a larger process. The final step of any workflow is to create the event for the *next* node in the chain and queue it for processing.
*   **Parallel Execution:** Scalability is achieved not by making a single task faster, but by running many tasks at once. We will scale our `celery_worker` service horizontally using Docker to process hundreds of URLs simultaneously.

## 3. The Feature Flow: A Multi-Phase Pipeline

The entire process is a pipeline where the output of one phase becomes the input for the next.

### Phase 1: URL Discovery

*   **Goal:** To generate a list of candidate URLs from a broad search query.
*   **Trigger:** A new API endpoint (e.g., `POST /discover`) receives a query like `{"query": "physical therapy clinics in San Diego"}`.
*   **Workflow:** `UrlDiscoveryWorkflow`
    1.  The API creates a single `Event` with `workflow_type = 'URL_DISCOVERY'`.
    2.  A Celery worker picks up this event and executes the workflow.
    3.  The workflow calls FireCrawl's `search()` API to get a list of URLs.
    4.  **Handoff:** The workflow then iterates through the discovered URLs. For each URL, it creates a *new* `Event` with `workflow_type = 'WEB_CRAWL'` and queues it for processing. This "fans out" one discovery job into many extraction jobs.

### Phase 2: Parallel Data Extraction

*   **Goal:** To crawl each individual website and extract its content.
*   **Trigger:** An `Event` with `workflow_type = 'WEB_CRAWL'`.
*   **Workflow:** `WebCrawlWorkflow`
    1.  This phase is massively parallel. We will run multiple `celery_worker` containers (`docker-compose up --scale celery_worker=10`).
    2.  Each worker independently picks up one `WEB_CRAWL` event.
    3.  The workflow calls FireCrawl's `scrape()` API for its assigned URL.
    4.  **Handoff:** Upon successful completion, the workflow creates a *new* `Event` with `workflow_type = 'VALIDATION'`, passing the scraped data as the input.

### Phase 3: LLM Validation

*   **Goal:** To use a Large Language Model to validate and clean the data from each website.
*   **Trigger:** An `Event` with `workflow_type = 'VALIDATION'`.
*   **Workflow:** `ValidationWorkflow`
    1.  A worker picks up the event containing the scraped data.
    2.  The workflow formats the data into a prompt for an LLM (e.g., "Does the following text describe a healthcare practice? Is there a list of services? Extract them into a valid JSON object.").
    3.  It calls the LLM and parses the structured response.
    4.  **Handoff (Conditional):** If the LLM validates the data as useful, the workflow creates a final `Event` with `workflow_type = 'STORAGE'`. If validation fails, the chain stops here for that URL.

### Phase 4: Data Storage

*   **Goal:** To save the clean, validated data to its final destination.
*   **Trigger:** An `Event` with `workflow_type = 'STORAGE'`.
*   **Workflow:** `StorageWorkflow`
    1.  A worker picks up the event containing the final, validated data.
    2.  The workflow connects to the database and saves the data into a new, clean table (e.g., `validated_practices`). This separates raw event logs from final, production-ready data.

---

## 4. Proposed File Structure

This plan involves creating new files and modifying existing ones.

```
spearmint/
├── app/
│   ├── api/
│   │   ├── router.py               # MODIFIED: Add the new /discover endpoint
│   │   └── discover_endpoint.py    # NEW: Endpoint to kick off the pipeline.
│   │
│   ├── services/
│   │   └── llm_service.py          # NEW (if not exists): A dedicated service for LLM calls.
│   │
│   └── workflows/
│       ├── workflow_registry.py      # MODIFIED: Register all new workflows.
│       ├── url_discovery_workflow.py # NEW: Implements Phase 1 logic.
│       ├── web_crawl_workflow.py     # NEW: Implements Phase 2 logic and chains to Phase 3.
│       ├── validation_workflow.py    # NEW: Implements Phase 3 logic and chains to Phase 4.
│       └── storage_workflow.py       # NEW: Implements Phase 4 logic.
│
└── FIRECRAWL_EXPANSION_PLAN.md       # THIS FILE
```

## 5. Key Relationships & How to Implement

1.  **API to Event:** The `discover_endpoint.py` will be responsible for creating the *first* `Event` in the chain (`URL_DISCOVERY`) and sending the task to Celery. This is the only manual task creation.

2.  **Event to Worker:** The `celery_worker` is always listening. The `app/worker/tasks.py` file, which contains `process_incoming_event`, acts as the central dispatcher. **It does not need to be modified.**

3.  **Worker to Workflow:** The dispatcher uses `app/workflows/workflow_registry.py` to find the correct workflow class based on the event's `workflow_type`.

4.  **Workflow to Next Workflow (Chaining):** This is the most critical concept. The `run` method of any given workflow (e.g., `WebCrawlWorkflow`) will be responsible for creating the *next* `Event` (e.g., for `VALIDATION`) and using `celery_app.send_task()` to place it on the queue. This is how nodes hand off information.

## 6. How to Run

To achieve the parallelism required for Phase 2, you will need to scale the number of Celery workers when starting Docker Compose.

```bash
# Run the application with 10 Celery workers ready to process extraction jobs
docker-compose up --build -d --scale celery_worker=10
``` 