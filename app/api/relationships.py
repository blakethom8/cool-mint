"""
Relationship Management API Endpoints

Provides RESTful endpoints for managing relationships between users
and contacts/providers/sites.
"""

from typing import List, Optional
from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from sqlalchemy.orm import Session

from database.session import db_session
from services.relationship_service import RelationshipService
from schemas.relationship_schema import (
    RelationshipListResponse,
    RelationshipDetail,
    RelationshipFilters,
    RelationshipUpdate,
    BulkRelationshipUpdate,
    RelationshipUpdateResponse,
    ActivityLogCreate,
    ActivityLogResponse,
    FilterOptionsResponse,
    ExportRequest,
    CreateRelationshipFromProvider
)

router = APIRouter()


@router.get("/", response_model=RelationshipListResponse)
async def list_relationships(
    # Pagination
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    sort_by: str = Query(
        "last_activity_date",
        description="Sort field",
        pattern="^(last_activity_date|entity_name|relationship_status|lead_score|created_at)$"
    ),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    
    # User filters
    user_ids: Optional[List[int]] = Query(None, description="Filter by user IDs"),
    my_relationships_only: bool = Query(False, description="Only show current user's relationships"),
    
    # Entity filters
    entity_type_ids: Optional[List[int]] = Query(None, description="Filter by entity type IDs"),
    entity_ids: Optional[List[UUID]] = Query(None, description="Filter by specific entity IDs"),
    
    # Status filters
    relationship_status_ids: Optional[List[int]] = Query(None, description="Filter by relationship status IDs"),
    loyalty_status_ids: Optional[List[int]] = Query(None, description="Filter by loyalty status IDs"),
    lead_scores: Optional[List[int]] = Query(None, description="Filter by lead scores (1-5)"),
    
    # Activity filters
    last_activity_after: Optional[date] = Query(None, description="Activities after this date"),
    last_activity_before: Optional[date] = Query(None, description="Activities before this date"),
    days_since_activity_min: Optional[int] = Query(None, description="Minimum days since last activity"),
    days_since_activity_max: Optional[int] = Query(None, description="Maximum days since last activity"),
    
    # Other filters
    campaign_ids: Optional[List[UUID]] = Query(None, description="Filter by campaign IDs"),
    search_text: Optional[str] = Query(None, description="Search in entity names and notes"),
    geographies: Optional[List[str]] = Query(None, description="Filter by geography"),
    cities: Optional[List[str]] = Query(None, description="Filter by city"),
    specialties: Optional[List[str]] = Query(None, description="Filter by specialty"),
    
    # Dependencies
    session: Session = Depends(db_session),
    # current_user would come from auth dependency
):
    """
    List relationships with filtering and pagination.
    
    Returns paginated list of relationships with their current status,
    metrics, and related information.
    """
    # Build filters object
    filters = RelationshipFilters(
        user_ids=user_ids,
        my_relationships_only=my_relationships_only,
        entity_type_ids=entity_type_ids,
        entity_ids=entity_ids,
        relationship_status_ids=relationship_status_ids,
        loyalty_status_ids=loyalty_status_ids,
        lead_scores=lead_scores,
        last_activity_after=last_activity_after,
        last_activity_before=last_activity_before,
        days_since_activity_min=days_since_activity_min,
        days_since_activity_max=days_since_activity_max,
        campaign_ids=campaign_ids,
        search_text=search_text,
        geographies=geographies,
        cities=cities,
        specialties=specialties
    )
    
    service = RelationshipService(session)
    items, total_count = service.list_relationships(
        filters=filters,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    total_pages = (total_count + page_size - 1) // page_size
    
    return RelationshipListResponse(
        items=items,
        total_count=total_count,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/filter-options", response_model=FilterOptionsResponse)
async def get_filter_options(
    session: Session = Depends(db_session)
):
    """
    Get available filter options for dropdowns.
    
    Returns lists of users, entity types, statuses, campaigns, etc.
    that can be used to populate filter dropdowns in the UI.
    """
    service = RelationshipService(session)
    options = service.get_filter_options()
    
    return FilterOptionsResponse(**options)


@router.get("/{relationship_id}", response_model=RelationshipDetail)
async def get_relationship_detail(
    relationship_id: UUID = Path(..., description="Relationship ID"),
    session: Session = Depends(db_session)
):
    """
    Get detailed information for a specific relationship.
    
    Includes full entity details, recent activities, metrics,
    and associated campaigns.
    """
    service = RelationshipService(session)
    relationship = service.get_relationship_detail(relationship_id)
    
    if not relationship:
        raise HTTPException(status_code=404, detail="Relationship not found")
        
    return relationship


@router.patch("/{relationship_id}", response_model=RelationshipDetail)
async def update_relationship(
    relationship_id: UUID = Path(..., description="Relationship ID"),
    updates: RelationshipUpdate = Body(..., description="Fields to update"),
    session: Session = Depends(db_session),
    # current_user would come from auth
):
    """
    Update a relationship's status, score, or other fields.
    
    Creates a history record for status changes.
    """
    service = RelationshipService(session)
    
    # TODO: Get current user ID from auth
    current_user_id = 1  # Placeholder
    
    updated = service.update_relationship(
        relationship_id=relationship_id,
        updates=updates,
        user_id=current_user_id
    )
    
    if not updated:
        raise HTTPException(status_code=404, detail="Relationship not found")
        
    return updated


@router.post("/bulk-update", response_model=RelationshipUpdateResponse)
async def bulk_update_relationships(
    bulk_update: BulkRelationshipUpdate = Body(...),
    session: Session = Depends(db_session)
):
    """
    Update multiple relationships at once.
    
    Useful for bulk status changes or score updates.
    """
    service = RelationshipService(session)
    
    # TODO: Get current user ID from auth
    current_user_id = 1  # Placeholder
    
    updated_relationships = []
    for rel_id in bulk_update.relationship_ids:
        updated = service.update_relationship(
            relationship_id=rel_id,
            updates=bulk_update.updates,
            user_id=current_user_id
        )
        if updated:
            # Convert detail to list item for response
            # This is simplified - would need proper conversion
            updated_relationships.append(updated)
    
    return RelationshipUpdateResponse(
        updated_count=len(updated_relationships),
        relationships=updated_relationships,
        message=f"Successfully updated {len(updated_relationships)} relationships"
    )


@router.get("/{relationship_id}/activities")
async def get_relationship_activities(
    relationship_id: UUID = Path(..., description="Relationship ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    session: Session = Depends(db_session)
):
    """
    Get activity history for a relationship.
    
    Returns paginated list of activities between the user and entity.
    """
    service = RelationshipService(session)
    relationship = service.get_relationship_detail(relationship_id)
    
    if not relationship:
        raise HTTPException(status_code=404, detail="Relationship not found")
    
    # Return recent activities from the detail (simplified)
    return {
        "activities": relationship.recent_activities,
        "total_count": len(relationship.recent_activities),
        "page": page,
        "page_size": page_size
    }


@router.post("/{relationship_id}/activities", response_model=ActivityLogResponse)
async def log_activity(
    relationship_id: UUID = Path(..., description="Relationship ID"),
    activity: ActivityLogCreate = Body(...),
    session: Session = Depends(db_session)
):
    """
    Log a new activity against a relationship.
    
    Updates the last activity date and related metrics.
    """
    # This would need implementation to:
    # 1. Create activity record
    # 2. Update relationship last_activity_date
    # 3. Recalculate metrics
    
    raise HTTPException(
        status_code=501,
        detail="Activity logging not yet implemented"
    )


@router.get("/{relationship_id}/metrics")
async def get_relationship_metrics(
    relationship_id: UUID = Path(..., description="Relationship ID"),
    session: Session = Depends(db_session)
):
    """
    Get detailed metrics for a relationship.
    
    Includes activity counts, engagement patterns, and trends.
    """
    service = RelationshipService(session)
    relationship = service.get_relationship_detail(relationship_id)
    
    if not relationship:
        raise HTTPException(status_code=404, detail="Relationship not found")
        
    return relationship.metrics


@router.post("/from-provider", response_model=RelationshipDetail)
async def create_relationship_from_provider(
    data: CreateRelationshipFromProvider = Body(...),
    session: Session = Depends(db_session)
):
    """
    Create a new relationship from a claims provider.
    
    This endpoint is used by the Market Explorer to add providers
    to the relationship management system. It also creates an
    associated note if provided.
    """
    service = RelationshipService(session)
    
    try:
        # Create the relationship and optional note
        relationship = service.create_from_provider(
            provider_id=data.provider_id,
            user_id=data.user_id,
            relationship_status_id=data.relationship_status_id,
            loyalty_status_id=data.loyalty_status_id,
            lead_score=data.lead_score,
            next_steps=data.next_steps,
            note_content=data.note_content
        )
        
        return relationship
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create relationship: {str(e)}"
        )


@router.post("/export")
async def export_relationships(
    export_request: ExportRequest = Body(...),
    session: Session = Depends(db_session)
):
    """
    Export relationships data to CSV or Excel.
    
    Applies filters and includes optional activity/metrics data.
    """
    # This would need implementation to:
    # 1. Apply filters
    # 2. Generate CSV/Excel file
    # 3. Return file download
    
    raise HTTPException(
        status_code=501,
        detail="Export functionality not yet implemented"
    )


# Error handlers
# Note: Exception handlers should be added to the main FastAPI app, not to routers
# @router.exception_handler(ValueError)
# async def value_error_handler(request, exc):
#     return HTTPException(status_code=400, detail=str(exc))


# @router.exception_handler(Exception)
# async def general_exception_handler(request, exc):
#     return HTTPException(status_code=500, detail="Internal server error")