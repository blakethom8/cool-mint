import json
from contextlib import contextmanager

from api.dependencies import db_session
from api.schemas.event import EventSchema
from models.orm.event import Event
from pipelines.registry import PipelineRegistry
from database.repository import GenericRepository
from tasks.celery_config import celery_app


@celery_app.task(name="process_event_task")
def process_event_task(event_id: str):
    with contextmanager(db_session)() as session:
        repository = GenericRepository(session=session, model=Event)
        db_event = repository.get(id=event_id)
        event = EventSchema(**db_event.data)
        pipeline = PipelineRegistry.get_pipeline(event)
        task_context = pipeline.run(event).model_dump_json()

        db_event.task_context = json.loads(task_context)
        repository.update(obj=db_event)
