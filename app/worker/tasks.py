from contextlib import contextmanager

from worker.config import celery_app
from database.event import Event
from database.repository import GenericRepository
from database.session import db_session
from workflows.workflow_registry import WorkflowRegistry

"""
Workflow Task Processing Module

This module handles asynchronous processing of workflow events using Celery.
It manages the lifecycle of event processing from database retrieval through
workflow execution and result storage.
"""


@celery_app.task(name="process_incoming_event")
def process_incoming_event(event_id: str):
    """Processes an incoming event through its designated workflow.

    This Celery task handles the asynchronous processing of events by:
    1. Retrieving the event from the database
    2. Determining the appropriate workflow
    3. Executing the workflow
    4. Storing the results

    Args:
        event_id: Unique identifier of the event to process
        workflow_type: Type of workflow to use for processing the event
    """
    with contextmanager(db_session)() as session:
        # Initialize repository for database operations
        repository = GenericRepository(session=session, model=Event)

        # Retrieve event from database
        db_event = repository.get(id=event_id)
        if db_event is None:
            raise ValueError(f"Event with id {event_id} not found")

        # Execute workflow and store results
        workflow = WorkflowRegistry[db_event.workflow_type].value()
        task_context = workflow.run(db_event.data).model_dump(mode="json")

        db_event.task_context = task_context

        # Update event with processing results
        repository.update(obj=db_event)


@celery_app.task(name="process_email_webhook")
def process_email_webhook(event_id: str):
    """Processes an incoming email webhook event.

    This Celery task handles the asynchronous processing of Nylas email webhooks by:
    1. Retrieving the webhook event from the database
    2. Extracting email details from the webhook payload
    3. Processing the email through the email workflow
    4. Storing the results

    Args:
        event_id: Unique identifier of the webhook event to process
    """
    with contextmanager(db_session)() as session:
        # Initialize repository for database operations
        repository = GenericRepository(session=session, model=Event)

        # Retrieve event from database
        db_event = repository.get(id=event_id)
        if db_event is None:
            raise ValueError(f"Event with id {event_id} not found")

        # Import the email service
        from services.nylas_email_service import NylasEmailService
        
        # Extract email data from webhook
        event_data = db_event.data
        trigger_type = event_data.get("trigger")
        object_data = event_data.get("object_data", {})
        grant_id = event_data.get("grant_id")

        print(f"Processing email webhook: {trigger_type} for grant {grant_id}")
        
        # Initialize email service
        email_service = NylasEmailService(session)
        
        # Process based on trigger type
        if trigger_type == "message.created":
            # Sync the email to database
            email = email_service.sync_email_from_webhook(event_data)
            
            if email:
                print(f"New email synced: {email.subject} (ID: {email.nylas_id})")
                
                # TODO: Trigger email processing workflow
                # This will be implemented after creating the workflow
                
                db_event.task_context = {
                    "status": "processed",
                    "trigger_type": trigger_type,
                    "email_id": email.nylas_id,
                    "db_email_id": str(email.id),
                    "subject": email.subject
                }
            else:
                db_event.task_context = {
                    "status": "error",
                    "trigger_type": trigger_type,
                    "error": "Failed to sync email"
                }
        else:
            # Handle other trigger types (message.updated, etc.)
            db_event.task_context = {
                "status": "processed",
                "trigger_type": trigger_type,
                "email_id": object_data.get("id")
            }
            
        repository.update(obj=db_event)
