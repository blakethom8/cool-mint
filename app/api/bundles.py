from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, desc
from sqlalchemy.orm import Session, selectinload
from uuid import UUID
import tiktoken

from database.session import db_session
from database.data_models.activity_bundles import ActivityBundle, LLMConversation
from database.data_models.salesforce_data import SfActivityStructured
from schemas.bundle_schema import (
    BundleResponse,
    BundleListResponse,
    BundleDetailResponse,
    BundleDeleteResponse,
)

router = APIRouter()


@router.get("/", response_model=BundleListResponse)
async def list_bundles(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    search: Optional[str] = Query(None),
    sort_by: str = Query("created_at", pattern="^(created_at|name|activity_count)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    session: Session = Depends(db_session)
):
    """
    List all activity bundles with pagination and search.
    
    Returns bundles with basic information including conversation count.
    """
    # Build base query
    query = select(ActivityBundle)
    
    # Apply search filter
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            ActivityBundle.name.ilike(search_pattern) |
            ActivityBundle.description.ilike(search_pattern)
        )
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_count = session.scalar(count_query)
    
    # Apply sorting
    sort_column = getattr(ActivityBundle, sort_by)
    if sort_order == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(sort_column)
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    # Load with conversation count
    query = query.options(selectinload(ActivityBundle.conversations))
    
    # Execute query
    bundles = session.scalars(query).all()
    
    # Convert to response model
    bundle_responses = []
    for bundle in bundles:
        response = BundleResponse.model_validate(bundle)
        response.conversation_count = len(bundle.conversations)
        bundle_responses.append(response)
    
    total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 0
    
    return BundleListResponse(
        bundles=bundle_responses,
        total_count=total_count,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{bundle_id}", response_model=BundleDetailResponse)
async def get_bundle_detail(
    bundle_id: UUID,
    session: Session = Depends(db_session)
):
    """
    Get detailed information for a specific bundle including activity data.
    
    Returns the bundle information along with the full activity data
    and LLM context for each activity in the bundle.
    """
    # Get bundle
    bundle = session.scalar(
        select(ActivityBundle)
        .where(ActivityBundle.id == bundle_id)
        .options(selectinload(ActivityBundle.conversations))
    )
    
    if not bundle:
        raise HTTPException(status_code=404, detail="Bundle not found")
    
    # Get activities for the bundle
    activities = session.scalars(
        select(SfActivityStructured).where(
            SfActivityStructured.salesforce_activity_id.in_(bundle.activity_ids)
        )
    ).all()
    
    # Build activity data
    activity_data = []
    total_tokens = 0
    
    try:
        encoding = tiktoken.encoding_for_model("gpt-4")
    except Exception:
        encoding = None
    
    for activity in activities:
        # Build activity info
        activity_info = {
            "activity_id": activity.salesforce_activity_id,
            "subject": activity.subject,
            "description": activity.description,
            "activity_date": str(activity.activity_date) if activity.activity_date else None,
            "owner_name": activity.user_name,
            "mno_type": activity.mno_type,
            "mno_subtype": activity.mno_subtype,
            "contact_count": activity.contact_count,
            "contact_names": activity.contact_names or [],
            "llm_context": activity.llm_context_json,
        }
        activity_data.append(activity_info)
        
        # Count tokens
        if encoding:
            text = f"{activity.subject or ''} {activity.description or ''} {str(activity.llm_context_json or '')}"
            total_tokens += len(encoding.encode(text))
        else:
            # Fallback estimation
            total_tokens += len(text) // 4
    
    # Build response
    bundle_response = BundleResponse.model_validate(bundle)
    bundle_response.conversation_count = len(bundle.conversations)
    
    return BundleDetailResponse(
        bundle=bundle_response,
        activities=activity_data,
        total_tokens=total_tokens,
    )


@router.delete("/{bundle_id}", response_model=BundleDeleteResponse)
async def delete_bundle(
    bundle_id: UUID,
    session: Session = Depends(db_session)
):
    """
    Delete a bundle and all associated conversations.
    
    This will cascade delete all conversations and saved responses
    associated with the bundle.
    """
    # Get bundle
    bundle = session.scalar(
        select(ActivityBundle).where(ActivityBundle.id == bundle_id)
    )
    
    if not bundle:
        raise HTTPException(status_code=404, detail="Bundle not found")
    
    # Delete bundle (cascades to conversations and saved responses)
    session.delete(bundle)
    session.commit()
    
    return BundleDeleteResponse(
        success=True,
        message=f"Bundle '{bundle.name}' deleted successfully"
    )