from typing import Optional, List
from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from database.session import db_session
from services.email_service import EmailService
# Import sync manager only when needed to avoid startup failures
# from services.email_sync_manager import EmailSyncManager
from worker.config import celery_app
from database.event import Event
from database.repository import GenericRepository
from workflows.workflow_registry import WorkflowRegistry


router = APIRouter(prefix="/emails", tags=["emails"])


# Request/Response models
class EmailResponse(BaseModel):
    id: str
    nylas_id: str
    subject: str
    snippet: Optional[str]
    from_email: Optional[str]
    from_name: Optional[str]
    to_emails: Optional[List[str]]
    date: Optional[str]
    unread: bool
    has_attachments: bool
    processed: bool
    processing_status: Optional[str]
    classification: Optional[str]
    is_forwarded: Optional[bool] = False
    user_instruction: Optional[str]
    created_at: str
    body_preview: Optional[str]


class EmailsListResponse(BaseModel):
    items: List[EmailResponse]
    total_count: int
    page: int
    page_size: int
    total_pages: int


class EmailDetailResponse(BaseModel):
    id: str
    nylas_id: str
    grant_id: str
    thread_id: str
    subject: str
    snippet: Optional[str]
    from_email: Optional[str]
    from_name: Optional[str]
    to_emails: Optional[List[str]]
    cc_emails: Optional[List[str]]
    bcc_emails: Optional[List[str]]
    date: Optional[str]
    body: Optional[str]
    body_plain: Optional[str]
    unread: bool
    starred: bool
    has_attachments: bool
    attachments_count: int
    processed: bool
    processing_status: Optional[str]
    classification: Optional[str]
    is_forwarded: bool
    user_instruction: Optional[str]
    extracted_thread: Optional[str]
    folders: Optional[List[str]]
    labels: Optional[List[str]]
    created_at: str
    updated_at: str


class SyncResponse(BaseModel):
    success: bool
    message: str
    total_fetched: int
    new_emails: int
    updated_emails: int
    sync_mode: str
    sync_time: str


class ProcessResponse(BaseModel):
    success: bool
    message: str
    email_id: str
    workflow_triggered: bool


@router.get("/", response_model=EmailsListResponse)
async def list_emails(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search_text: Optional[str] = Query(None, description="Search in subject, body, or from"),
    from_email: Optional[str] = Query(None, description="Filter by sender email"),
    processed: Optional[bool] = Query(None, description="Filter by processed status"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    sort_by: str = Query('date', description="Sort field"),
    sort_order: str = Query('desc', regex="^(asc|desc)$"),
    db: Session = Depends(db_session)
):
    """
    List emails with filtering and pagination.
    
    Returns emails sorted by date (newest first by default).
    """
    service = EmailService(db)
    
    items, total_count = service.list_emails(
        page=page,
        page_size=page_size,
        search_text=search_text,
        from_email=from_email,
        processed=processed,
        start_date=start_date,
        end_date=end_date,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    total_pages = (total_count + page_size - 1) // page_size
    
    # Convert to response models
    response_items = [EmailResponse(**item) for item in items]
    
    return EmailsListResponse(
        items=response_items,
        total_count=total_count,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/{email_id}", response_model=EmailDetailResponse)
async def get_email_detail(
    email_id: UUID,
    db: Session = Depends(db_session)
):
    """
    Get detailed information about a specific email.
    """
    service = EmailService(db)
    email = service.get_email_detail(email_id)
    
    if not email:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email not found"
        )
    
    return EmailDetailResponse(**email)


@router.post("/sync", response_model=SyncResponse)
async def sync_emails(
    minutes_back: int = Query(30, description="How many minutes back to sync"),
    limit: int = Query(50, description="Maximum emails to sync"),
    db: Session = Depends(db_session)
):
    """
    Trigger manual email sync from Nylas.
    
    This fetches recent emails and stores them in the database.
    """
    try:
        # Import here to avoid startup issues if nylas not installed
        from services.email_sync_manager import EmailSyncManager
        
        sync_manager = EmailSyncManager()
        
        # Run sync - process_emails=False to avoid auto-processing
        results = sync_manager.sync_recent_emails(
            minutes_back=minutes_back,
            limit=limit,
            process_emails=False
        )
        
        return SyncResponse(
            success=True,
            message=f"Successfully synced {results['new_emails']} new emails",
            total_fetched=results['total_fetched'],
            new_emails=results['new_emails'],
            updated_emails=results['updated_emails'],
            sync_mode=results['sync_mode'],
            sync_time=results['sync_time']
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Email sync failed: {str(e)}"
        )


@router.post("/{email_id}/process", response_model=ProcessResponse)
async def process_email(
    email_id: UUID,
    db: Session = Depends(db_session)
):
    """
    Process an email through the EMAIL_ACTIONS workflow.
    
    This triggers AI classification and action extraction.
    """
    service = EmailService(db)
    email = service.get_email_detail(email_id)
    
    if not email:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email not found"
        )
    
    # Commented out for debugging - allow reprocessing
    # if email['processed'] and email['processing_status'] == 'completed':
    #     return ProcessResponse(
    #         success=True,
    #         message="Email has already been processed",
    #         email_id=str(email_id),
    #         workflow_triggered=False
    #     )
    
    try:
        # Mark email as being processed
        service.mark_email_processed(email_id, status='in_progress')
        
        # Prepare event data for workflow
        event_data = {
            "email_id": str(email_id),
            "content": email['body'] or email['body_plain'] or '',
            "subject": email['subject'],
            "from_email": email['from_email'] or 'unknown',
            "is_forwarded": email['is_forwarded'],
            "user_instruction": email['user_instruction']
        }
        
        # Store event in database for Celery processing
        repository = GenericRepository(session=db, model=Event)
        event = Event(
            data=event_data,
            workflow_type=WorkflowRegistry.EMAIL_ACTIONS.name
        )
        repository.create(obj=event)
        
        # Queue processing task
        task_id = celery_app.send_task(
            "process_incoming_event",
            args=[str(event.id)]
        )
        
        return ProcessResponse(
            success=True,
            message=f"Email processing started (task: {task_id}). Check pending actions soon.",
            email_id=str(email_id),
            workflow_triggered=True
        )
    
    except Exception as e:
        # Mark as failed
        service.mark_email_processed(email_id, status='error')
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process email: {str(e)}"
        )


