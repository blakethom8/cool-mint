from fastapi import APIRouter

from api import endpoint, activities, bundles, llm, contacts, claims, relationships, email_webhook, email_actions, emails

"""
API Router Module

This module sets up the API router and includes all defined endpoints.
It uses FastAPI's APIRouter to group related endpoints and provide a prefix.
"""

router = APIRouter()

router.include_router(endpoint.router, prefix="/events", tags=["events"])
router.include_router(activities.router, prefix="/activities", tags=["activities"])
router.include_router(bundles.router, prefix="/bundles", tags=["bundles"])
router.include_router(llm.router, prefix="/llm", tags=["llm"])
router.include_router(contacts.router, prefix="/contacts", tags=["contacts"])
router.include_router(claims.router, tags=["claims"])
router.include_router(relationships.router, prefix="/relationships", tags=["relationships"])
router.include_router(email_webhook.router, prefix="/webhooks", tags=["webhooks"])
router.include_router(email_actions.router, tags=["email-actions"])
router.include_router(emails.router, tags=["emails"])
