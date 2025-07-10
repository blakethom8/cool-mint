from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, and_, or_, any_
from sqlalchemy.orm import Session

from database.session import db_session
from database.data_models.salesforce_data import SfActivityStructured
from schemas.activity_api_schema import (
    ActivityListItem,
    ActivityDetail,
    ActivityListResponse,
    FilterOptionsResponse,
    ActivitySelectionRequest,
    ActivityContactInfo,
)

router = APIRouter()


@router.get("/", response_model=ActivityListResponse)
async def list_activities(
    # Pagination parameters
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    sort_by: str = Query(
        "activity_date", pattern="^(activity_date|subject|owner_name|created_at)$"
    ),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    # Filter parameters
    owner_ids: Optional[List[str]] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    search_text: Optional[str] = Query(None),
    has_contact: Optional[bool] = Query(None),
    has_md_contact: Optional[bool] = Query(None),
    has_pharma_contact: Optional[bool] = Query(None),
    contact_specialties: Optional[List[str]] = Query(None),
    mno_types: Optional[List[str]] = Query(None),
    mno_subtypes: Optional[List[str]] = Query(None),
    statuses: Optional[List[str]] = Query(None),
    types: Optional[List[str]] = Query(None),
    session: Session = Depends(db_session),
):
    """
    List activities with filtering and pagination.

    This endpoint returns a paginated list of activities from the structured
    activities table, with support for various filters including:
    - Date range
    - Owner/user filtering
    - Text search in subject and description
    - Contact type filtering
    - Activity type and status filtering
    """
    # Build base query
    query = select(SfActivityStructured)

    # Apply filters
    filters = []

    if owner_ids:
        filters.append(SfActivityStructured.owner_id.in_(owner_ids))

    if start_date:
        filters.append(SfActivityStructured.activity_date >= start_date)

    if end_date:
        filters.append(SfActivityStructured.activity_date <= end_date)

    if search_text:
        search_pattern = f"%{search_text}%"
        filters.append(
            or_(
                SfActivityStructured.subject.ilike(search_pattern),
                SfActivityStructured.description.ilike(search_pattern),
                any_(SfActivityStructured.contact_names).ilike(search_pattern),
            )
        )

    if has_contact is not None:
        if has_contact:
            filters.append(SfActivityStructured.contact_count > 0)
        else:
            filters.append(SfActivityStructured.contact_count == 0)

    if has_md_contact is not None:
        filters.append(SfActivityStructured.activity_has_physicians == has_md_contact)

    if has_pharma_contact is not None:
        # Since we don't have a pharma field, this filter is ignored for now
        pass

    if contact_specialties:
        # Check if any of the specialties match
        specialty_filters = []
        for specialty in contact_specialties:
            specialty_filters.append(
                SfActivityStructured.contact_specialties.contains([specialty])
            )
        filters.append(or_(*specialty_filters))

    if mno_types:
        filters.append(SfActivityStructured.mno_type.in_(mno_types))

    if mno_subtypes:
        filters.append(SfActivityStructured.mno_subtype.in_(mno_subtypes))

    if statuses:
        filters.append(SfActivityStructured.status.in_(statuses))

    if types:
        filters.append(SfActivityStructured.type.in_(types))

    if filters:
        query = query.where(and_(*filters))

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_count = session.scalar(count_query)

    # Apply sorting
    sort_column = getattr(SfActivityStructured, sort_by)
    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    # Execute query
    activities = session.scalars(query).all()

    # Convert to response model
    activity_items = []
    for activity in activities:
        activity_items.append(
            ActivityListItem(
                id=str(activity.id),
                activity_id=activity.salesforce_activity_id,
                activity_date=activity.activity_date,
                subject=activity.subject,
                description=activity.description,
                mno_type=activity.mno_type,
                mno_subtype=activity.mno_subtype,
                owner_name=activity.user_name,
                owner_id=activity.owner_id,
                status=activity.status,
                priority=activity.priority,
                type=activity.type,
                contact_count=activity.contact_count,
                contact_names=activity.contact_names or [],
                contact_specialties=activity.contact_specialties or [],
                has_contact=activity.contact_count > 0,
                has_md_contact=activity.activity_has_physicians,
                has_pharma_contact=False,  # This field doesn't exist in the current schema
                has_other_contact=activity.contact_count > 0 and not activity.activity_has_physicians,
            )
        )

    total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 0

    return ActivityListResponse(
        activities=activity_items,
        total_count=total_count,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/filter-options", response_model=FilterOptionsResponse)
async def get_filter_options(session: Session = Depends(db_session)):
    """
    Get available filter options for the activity list.

    Returns distinct values for various filter fields to populate
    dropdown menus and filter controls in the UI.
    """
    # Get distinct owners
    owner_query = (
        select(SfActivityStructured.owner_id, SfActivityStructured.user_name)
        .distinct()
        .where(SfActivityStructured.owner_id.isnot(None))
        .order_by(SfActivityStructured.user_name)
    )
    owners_result = session.execute(owner_query).all()
    owners = [
        {"id": owner_id, "name": owner_name}
        for owner_id, owner_name in owners_result
        if owner_name
    ]

    # Get distinct specialties
    specialty_query = (
        select(func.unnest(SfActivityStructured.contact_specialties))
        .distinct()
        .where(SfActivityStructured.contact_specialties.isnot(None))
    )
    specialties = [s for s in session.scalars(specialty_query).all() if s]
    specialties.sort()

    # Get distinct MNO types
    mno_type_query = (
        select(SfActivityStructured.mno_type)
        .distinct()
        .where(SfActivityStructured.mno_type.isnot(None))
    )
    mno_types = sorted(session.scalars(mno_type_query).all())

    # Get distinct MNO subtypes
    mno_subtype_query = (
        select(SfActivityStructured.mno_subtype)
        .distinct()
        .where(SfActivityStructured.mno_subtype.isnot(None))
    )
    mno_subtypes = sorted(session.scalars(mno_subtype_query).all())

    # Get distinct statuses
    status_query = (
        select(SfActivityStructured.status)
        .distinct()
        .where(SfActivityStructured.status.isnot(None))
    )
    statuses = sorted(session.scalars(status_query).all())

    # Get distinct types
    type_query = (
        select(SfActivityStructured.type)
        .distinct()
        .where(SfActivityStructured.type.isnot(None))
    )
    types = sorted(session.scalars(type_query).all())

    return FilterOptionsResponse(
        owners=owners,
        contact_specialties=specialties,
        mno_types=mno_types,
        mno_subtypes=mno_subtypes,
        statuses=statuses,
        types=types,
    )


@router.get("/{activity_id}", response_model=ActivityDetail)
async def get_activity(activity_id: str, session: Session = Depends(db_session)):
    """
    Get detailed information for a specific activity.

    Returns the full activity details including the complete LLM context JSON.
    """
    activity = session.scalar(
        select(SfActivityStructured).where(
            SfActivityStructured.salesforce_activity_id == activity_id
        )
    )

    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Parse contacts from llm_context_json
    contacts = []
    if activity.llm_context_json and "contacts" in activity.llm_context_json:
        for contact in activity.llm_context_json["contacts"]:
            contacts.append(
                ActivityContactInfo(
                    contact_id=contact.get("contact_id", ""),
                    contact_name=contact.get("contact_name", ""),
                    contact_type=contact.get("contact_type"),
                    specialty=contact.get("specialty"),
                    organization=contact.get("organization"),
                    city=contact.get("city"),
                )
            )

    return ActivityDetail(
        id=str(activity.id),
        activity_id=activity.salesforce_activity_id,
        activity_date=activity.activity_date,
        subject=activity.subject,
        description=activity.description,
        mno_type=activity.mno_type,
        mno_subtype=activity.mno_subtype,
        owner_name=activity.user_name,
        owner_id=activity.owner_id,
        status=activity.status,
        priority=activity.priority,
        type=activity.type,
        due_date=None,  # Field doesn't exist in current schema
        completed_date=None,  # Field doesn't exist in current schema
        contacts=contacts,
        llm_context_json=activity.llm_context_json,
        created_at=activity.structured_at,
        updated_at=activity.structured_at,
    )


@router.post("/selection")
async def process_activity_selection(
    request: ActivitySelectionRequest, session: Session = Depends(db_session)
):
    """
    Process selected activities for LLM analysis.

    This endpoint receives a list of activity IDs that the user has selected
    and prepares them for LLM processing. For now, it returns the selected
    activities' data. In the future, this will trigger LLM processing.
    """
    # Validate that all activity IDs exist
    activities = session.scalars(
        select(SfActivityStructured).where(
            SfActivityStructured.salesforce_activity_id.in_(request.activity_ids)
        )
    ).all()

    if len(activities) != len(request.activity_ids):
        found_ids = {a.salesforce_activity_id for a in activities}
        missing_ids = set(request.activity_ids) - found_ids
        raise HTTPException(
            status_code=400, detail=f"Some activity IDs not found: {list(missing_ids)}"
        )

    # For now, return the LLM context for the selected activities
    # In the future, this would trigger actual LLM processing
    llm_contexts = []
    for activity in activities:
        if activity.llm_context_json:
            llm_contexts.append(
                {
                    "activity_id": activity.salesforce_activity_id,
                    "context": activity.llm_context_json,
                }
            )

    return {
        "selected_count": len(activities),
        "activity_ids": request.activity_ids,
        "llm_contexts": llm_contexts,
        "message": "Activities selected successfully. Ready for LLM processing.",
    }
