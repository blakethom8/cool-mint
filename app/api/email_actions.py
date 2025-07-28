from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from database.session import db_session
from services.email_actions_service import EmailActionsService


router = APIRouter(prefix="/email-actions", tags=["email-actions"])


# Request/Response models
class EmailActionUpdateRequest(BaseModel):
    status: Optional[str] = Field(None, description="New status")
    review_notes: Optional[str] = Field(None, description="Review notes")
    staging_updates: Optional[Dict[str, Any]] = Field(None, description="Updates to staging data")


class EmailActionResponse(BaseModel):
    id: str
    email_id: str
    action_type: str
    action_parameters: Optional[Dict[str, Any]] = None
    confidence_score: float
    reasoning: str
    status: str
    reviewed_at: Optional[str] = None
    reviewed_by: Optional[str] = None
    review_notes: Optional[str] = None
    created_at: str
    updated_at: str
    email: Dict[str, Any]
    staging_data: Optional[Dict[str, Any]] = None


class EmailActionsListResponse(BaseModel):
    items: List[EmailActionResponse]
    total_count: int
    page: int
    page_size: int
    total_pages: int


class DashboardStatsResponse(BaseModel):
    total_actions: int
    pending_actions: int
    approved_actions: int
    rejected_actions: int
    completed_actions: int
    action_type_breakdown: Dict[str, int]
    recent_actions_7_days: int
    average_confidence_score: float
    last_updated: str


class ActionResultResponse(BaseModel):
    success: bool
    message: str
    action_id: str


@router.get("/", response_model=EmailActionsListResponse)
async def list_email_actions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, description="Filter by status"),
    action_types: Optional[List[str]] = Query(None, description="Filter by action types"),
    user_email: Optional[str] = Query(None, description="Filter by user email"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    search_text: Optional[str] = Query(None, description="Search in email content"),
    sort_by: str = Query('created_at', description="Sort field"),
    sort_order: str = Query('desc', regex="^(asc|desc)$"),
    db: Session = Depends(db_session)
):
    """
    List email actions with filtering and pagination.
    
    This endpoint returns all email actions that are pending review or have been processed.
    """
    service = EmailActionsService(db)
    
    items, total_count = service.list_email_actions(
        page=page,
        page_size=page_size,
        status=status,
        action_types=action_types,
        user_email=user_email,
        start_date=start_date,
        end_date=end_date,
        search_text=search_text,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    total_pages = (total_count + page_size - 1) // page_size
    
    # Convert dictionary items to EmailActionResponse objects
    response_items = [EmailActionResponse(**item) for item in items]
    
    return EmailActionsListResponse(
        items=response_items,
        total_count=total_count,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/debug", response_model=dict)
async def debug_email_actions(
    db: Session = Depends(db_session)
):
    """
    Debug endpoint to check raw email actions data
    """
    from database.data_models.email_actions import EmailAction
    from database.data_models.email_data import Email
    
    # Get raw count
    count = db.query(EmailAction).count()
    
    # Get first action with details
    action = db.query(EmailAction).first()
    
    if action:
        # Check if email relationship exists
        email = db.query(Email).filter(Email.id == action.email_id).first()
        
        return {
            "total_actions": count,
            "first_action": {
                "id": str(action.id),
                "email_id": str(action.email_id),
                "action_type": action.action_type,
                "status": action.status,
                "has_email": email is not None,
                "email_exists_in_db": email is not None,
                "email_id_value": str(action.email_id) if action.email_id else None
            }
        }
    
    return {"total_actions": count, "message": "No actions found"}


@router.get("/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(
    db: Session = Depends(db_session)
):
    """
    Get dashboard statistics for email actions.
    
    Returns aggregated statistics about email actions for the dashboard.
    """
    service = EmailActionsService(db)
    stats = service.get_dashboard_stats(user_id=None)
    
    return DashboardStatsResponse(**stats)


@router.get("/{action_id}", response_model=EmailActionResponse)
async def get_email_action_detail(
    action_id: UUID,
    db: Session = Depends(db_session)
):
    """
    Get detailed information about a specific email action.
    
    Includes full email content and all staging data.
    """
    service = EmailActionsService(db)
    action = service.get_email_action_detail(action_id)
    
    if not action:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email action not found"
        )
    
    return EmailActionResponse(**action)


@router.patch("/{action_id}", response_model=EmailActionResponse)
async def update_email_action(
    action_id: UUID,
    request: EmailActionUpdateRequest,
    db: Session = Depends(db_session)
):
    """
    Update an email action and its staging data.
    
    Allows updating status, review notes, and staging data fields.
    """
    service = EmailActionsService(db)
    
    updates = {}
    if request.status is not None:
        updates['status'] = request.status
    if request.review_notes is not None:
        updates['review_notes'] = request.review_notes
    if request.staging_updates is not None:
        updates['staging_updates'] = request.staging_updates
    
    action = service.update_email_action(
        action_id=action_id,
        updates=updates,
        user_id=None
    )
    
    if not action:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email action not found"
        )
    
    return EmailActionResponse(**action)


@router.post("/{action_id}/approve", response_model=ActionResultResponse)
async def approve_email_action(
    action_id: UUID,
    db: Session = Depends(db_session)
):
    """
    Approve an email action (placeholder endpoint).
    
    This is a placeholder that will eventually trigger the action execution.
    For now, it just updates the status and returns a success message.
    """
    service = EmailActionsService(db)
    
    # Update status to approved
    action = service.update_email_action(
        action_id=action_id,
        updates={
            'status': 'approved',
            'review_notes': 'Approved by user'
        },
        user_id=None
    )
    
    if not action:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email action not found"
        )
    
    return ActionResultResponse(
        success=True,
        message=f"Action approved successfully. This action will be processed shortly by Juno.",
        action_id=str(action_id)
    )


@router.post("/{action_id}/reject", response_model=ActionResultResponse)
async def reject_email_action(
    action_id: UUID,
    reason: Optional[str] = Query(None, description="Reason for rejection"),
    db: Session = Depends(db_session)
):
    """
    Reject an email action (placeholder endpoint).
    
    This is a placeholder that marks the action as rejected.
    """
    service = EmailActionsService(db)
    
    # Update status to rejected
    review_notes = "Rejected by user"
    if reason:
        review_notes += f": {reason}"
    
    action = service.update_email_action(
        action_id=action_id,
        updates={
            'status': 'rejected',
            'review_notes': review_notes
        },
        user_id=None
    )
    
    if not action:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email action not found"
        )
    
    return ActionResultResponse(
        success=True,
        message="Action rejected successfully. Juno will learn from this feedback.",
        action_id=str(action_id)
    )