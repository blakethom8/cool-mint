import json
import os
import hashlib
import hmac
from http import HTTPStatus
from typing import Dict, Any

from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette.responses import Response

from worker.config import celery_app
from database.event import Event
from database.repository import GenericRepository
from database.session import db_session

router = APIRouter()


def verify_webhook_signature(
    body: bytes,
    signature: str,
    webhook_secret: str
) -> bool:
    """
    Verify the webhook signature from Nylas.
    
    Args:
        body: Raw request body
        signature: X-Webhook-Signature header value
        webhook_secret: Webhook secret from environment
        
    Returns:
        bool: True if signature is valid
    """
    expected_signature = hmac.new(
        webhook_secret.encode('utf-8'),
        body,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)


@router.post("/nylas")
async def handle_nylas_webhook(
    request: Request,
    session: Session = Depends(db_session),
) -> Response:
    """
    Handle incoming Nylas webhook events.
    
    This endpoint:
    1. Validates the webhook signature
    2. Stores the webhook event in the database
    3. Queues it for async processing
    4. Returns 200 OK to acknowledge receipt
    
    Args:
        request: Raw FastAPI request object
        session: Database session
        
    Returns:
        Response: 200 OK on success
    """
    # Get webhook secret from environment
    webhook_secret = os.environ.get("WEBHOOK_SECRET")
    if not webhook_secret:
        raise HTTPException(
            status_code=500,
            detail="Webhook secret not configured"
        )
    
    # Get raw body and signature
    body = await request.body()
    signature = request.headers.get("X-Webhook-Signature", "")
    
    # Verify signature
    if not verify_webhook_signature(body, signature, webhook_secret):
        raise HTTPException(
            status_code=401,
            detail="Invalid webhook signature"
        )
    
    # Parse webhook data
    try:
        webhook_data = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400,
            detail="Invalid JSON in request body"
        )
    
    # Extract webhook details
    deltas = webhook_data.get("deltas", [])
    
    # Process each delta (email event)
    for delta in deltas:
        # Store event in database
        repository = GenericRepository(
            session=session,
            model=Event,
        )
        
        event_data = {
            "type": "nylas_webhook",
            "trigger": delta.get("type"),
            "object_data": delta.get("object_data", {}),
            "grant_id": delta.get("grant_id"),
            "raw_webhook": webhook_data
        }
        
        event = Event(
            data=event_data,
            workflow_type="EMAIL_PROCESSING"  # We'll define this workflow type
        )
        repository.create(obj=event)
        
        # Queue processing task
        task_id = celery_app.send_task(
            "process_email_webhook",
            args=[str(event.id)],
        )
        
        print(f"Queued email processing task: {task_id}")
    
    # Return success response
    return Response(
        content=json.dumps({"status": "success", "events_processed": len(deltas)}),
        status_code=HTTPStatus.OK,
    )


@router.get("/nylas/health")
async def webhook_health() -> Dict[str, Any]:
    """
    Health check endpoint for webhook testing.
    
    Returns:
        Dict with health status and configuration info
    """
    return {
        "status": "healthy",
        "webhook_configured": bool(os.environ.get("WEBHOOK_SECRET")),
        "grant_id_configured": bool(os.environ.get("NYLAS_GRANT_ID")),
        "server_url": os.environ.get("SERVER_URL", "Not configured")
    }