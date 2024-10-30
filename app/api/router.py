from fastapi import APIRouter

from api import endpoint

router = APIRouter()

router.include_router(endpoint.router, prefix="/events", tags=["events"])
