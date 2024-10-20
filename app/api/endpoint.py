import json
from http import HTTPStatus

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from starlette.responses import Response

from api.dependencies import db_session
from api.event_schema import EventSchema
from database.event import Event
from database.repository import GenericRepository
from config.celery_config import celery_app

router = APIRouter()


@router.post("/", dependencies=[])
def handle_event(
    data: EventSchema,
    session: Session = Depends(db_session),
):
    repository = GenericRepository(
        session=session,
        model=Event,
    )
    event = Event(data=data.model_dump(mode="json"))
    repository.create(obj=event)

    task_id = celery_app.send_task(
        "process_incoming_event",
        args=[str(event.id)],
    )

    return Response(
        content=json.dumps({"message": f"process_incoming_event started `{task_id}` "}),
        status_code=HTTPStatus.ACCEPTED,
    )
