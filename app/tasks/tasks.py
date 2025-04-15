from contextlib import contextmanager

from config.celery_config import celery_app
from database.event import Event
from database.repository import GenericRepository
from database.session import db_session
from pipelines.registry import PipelineRegistry, PipelineType

"""
Pipeline Task Processing Module

This module handles asynchronous processing of pipeline events using Celery.
It manages the lifecycle of event processing from database retrieval through
pipeline execution and result storage.
"""


@celery_app.task(name="process_incoming_event")
def process_incoming_event(event_id: str, pipeline_type: PipelineType):
    """Processes an incoming event through its designated pipeline.

    This Celery task handles the asynchronous processing of events by:
    1. Retrieving the event from the database
    2. Determining the appropriate pipeline
    3. Executing the pipeline
    4. Storing the results

    Args:
        event_id: Unique identifier of the event to process
        pipeline_type: Type of pipeline to use for processing the event
    """
    with contextmanager(db_session)() as session:
        # Initialize repository for database operations
        repository = GenericRepository(session=session, model=Event)

        # Retrieve event from database
        db_event = repository.get(id=event_id)
        if db_event is None:
            raise ValueError(f"Event with id {event_id} not found")

        pipeline = PipelineRegistry().get_pipeline(pipeline_type)

        # Execute pipeline and store results
        task_context = pipeline.run(db_event.data).model_dump(mode="json")
        db_event.task_context = task_context

        # Update event with processing results
        repository.update(obj=db_event)
