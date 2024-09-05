from fastapi import APIRouter

from api.endpoints import event

router = APIRouter()

router.include_router(event.router, prefix="/events", tags=["events"])
