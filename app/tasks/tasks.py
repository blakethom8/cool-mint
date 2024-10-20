from contextlib import contextmanager

from api.dependencies import db_session
from api.event_schema import EventSchema
from config.celery_config import celery_app
from database.event import Event
from database.repository import GenericRepository
from pipelines.registry import PipelineRegistry


@celery_app.task(name="process_incoming_event")
def process_incoming_event(event_id: str):
    """
    Process an event task.

    Args:
        event_id (str): The ID of the event to process.

    Raises:
        ValueError: If the event is not found.
    """
    with contextmanager(db_session)() as session:
        repository = GenericRepository(session=session, model=Event)
        db_event = repository.get(id=event_id)
        if db_event is None:
            raise ValueError(f"Event with id {event_id} not found")

        event = EventSchema(**db_event.data)
        pipeline = PipelineRegistry.get_pipeline(event)

        task_context = pipeline.run(event).model_dump(mode="json")
        db_event.task_context = task_context

        repository.update(obj=db_event)
