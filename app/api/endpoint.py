import json
from http import HTTPStatus
from typing import Dict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from starlette.responses import Response

from schemas.langfuse_tracing_schema import LangfuseTracingEventSchema
from worker.config import celery_app
from database.event import Event
from database.repository import GenericRepository
from database.session import db_session

from workflows.workflow_registry import WorkflowRegistry

"""
Event Submission Endpoint Module

This module defines the primary FastAPI endpoint for event ingestion.
It implements the initial handling of incoming events by:
1. Validating the incoming event data
2. Persisting the event to the database
3. Queuing an asynchronous processing task
4. Returning an acceptance response

The endpoint follows the "accept-and-delegate" pattern where:
- Events are immediately accepted if valid
- Processing is handled asynchronously via Celery
- A 202 Accepted response indicates successful queueing

This pattern ensures high availability and responsiveness of the API
while allowing for potentially long-running processing operations.
"""

router = APIRouter()


@router.post("/", dependencies=[])
def handle_event(
    data: LangfuseTracingEventSchema,
    session: Session = Depends(db_session),
) -> Response:
    """Handles incoming event submissions.

    This endpoint receives events, stores them in the database,
    and queues them for asynchronous processing. It implements
    a non-blocking pattern to ensure API responsiveness.

    Args:
        data: The event data, validated against EventSchema
        session: Database session injected by FastAPI dependency

    Returns:
        Response: 202 Accepted response with task ID

    Note:
        The endpoint returns immediately after queueing the task.
        Use the task ID in the response to check processing status.
    """
    # Store event in database
    repository = GenericRepository(
        session=session,
        model=Event,
    )
    raw_event = data.model_dump(mode="json")
    event = Event(data=raw_event, workflow_type=get_workflow_type(raw_event))
    repository.create(obj=event)

    # Queue processing task
    task_id = celery_app.send_task(
        "process_incoming_event",
        args=[str(event.id)],
    )

    # Return acceptance response
    return Response(
        content=json.dumps({"message": f"process_incoming_event started `{task_id}` "}),
        status_code=HTTPStatus.ACCEPTED,
    )


def get_workflow_type(data: Dict) -> str:
    """
    Implement your logic to determine the workflow type based on the event data.
    """
    return WorkflowRegistry.LANGFUSE_TRACING.name
