from typing import List, Optional, Dict
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, and_, or_, distinct
from sqlalchemy.orm import Session

from database.session import db_session
from database.data_models.salesforce_data import SfContact
from schemas.contact_schema import (
    ContactMapMarker,
    ContactListItem,
    ContactDetail,
    ContactFilterOptions,
    ContactFilters,
    ContactListResponse,
    ContactMapResponse,
)

router = APIRouter()


@router.get("/map-data", response_model=ContactMapResponse)
async def get_map_data(
    # Geographic bounds
    north: Optional[float] = Query(None),
    south: Optional[float] = Query(None),
    east: Optional[float] = Query(None),
    west: Optional[float] = Query(None),
    # Filters
    specialty: Optional[str] = Query(None),
    organization: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    is_physician: Optional[bool] = Query(None),
    active: Optional[bool] = Query(True),
    search: Optional[str] = Query(None),
    session: Session = Depends(db_session),
):
    """
    Get contact data optimized for map markers.
    
    This endpoint returns minimal contact data for displaying on a map,
    with contacts grouped by address to show density.
    """
    # Build base query
    query = select(
        SfContact.id,
        SfContact.salesforce_id,
        SfContact.name,
        SfContact.mailing_latitude,
        SfContact.mailing_longitude,
        SfContact.mailing_address_compound,
        SfContact.specialty,
        SfContact.contact_account_name,
        func.count(SfContact.id).over(
            partition_by=[SfContact.mailing_latitude, SfContact.mailing_longitude]
        ).label("contact_count"),
    )
    
    # Apply filters
    filters = []
    
    # Geographic bounds filter
    if all([north, south, east, west]):
        filters.extend([
            SfContact.mailing_latitude.between(south, north),
            SfContact.mailing_longitude.between(west, east),
        ])
    
    # Only include contacts with valid coordinates
    filters.extend([
        SfContact.mailing_latitude.isnot(None),
        SfContact.mailing_longitude.isnot(None),
    ])
    
    if specialty:
        filters.append(SfContact.specialty == specialty)
    
    if organization:
        filters.append(SfContact.contact_account_name.ilike(f"%{organization}%"))
    
    if city:
        filters.append(SfContact.mailing_city == city)
    
    if state:
        filters.append(SfContact.mailing_state == state)
    
    if is_physician is not None:
        filters.append(SfContact.is_physician == is_physician)
    
    if active is not None:
        filters.append(SfContact.active == active)
    
    if search:
        search_pattern = f"%{search}%"
        filters.append(
            or_(
                SfContact.name.ilike(search_pattern),
                SfContact.first_name.ilike(search_pattern),
                SfContact.last_name.ilike(search_pattern),
                SfContact.specialty.ilike(search_pattern),
            )
        )
    
    if filters:
        query = query.where(and_(*filters))
    
    # Execute query
    results = session.execute(query).all()
    
    # Transform to map markers (deduplicate by location)
    seen_locations = set()
    markers = []
    
    for row in results:
        location_key = (row.mailing_latitude, row.mailing_longitude)
        if location_key not in seen_locations:
            seen_locations.add(location_key)
            markers.append(
                ContactMapMarker(
                    id=str(row.id),
                    salesforce_id=row.salesforce_id,
                    name=row.name,
                    latitude=row.mailing_latitude,
                    longitude=row.mailing_longitude,
                    mailing_address=row.mailing_address_compound,
                    contact_count=row.contact_count,
                    specialty=row.specialty,
                    organization=row.contact_account_name,
                )
            )
    
    # Calculate bounds if not provided
    bounds = None
    if markers and not all([north, south, east, west]):
        lats = [m.latitude for m in markers if m.latitude]
        lngs = [m.longitude for m in markers if m.longitude]
        if lats and lngs:
            bounds = {
                "north": max(lats),
                "south": min(lats),
                "east": max(lngs),
                "west": min(lngs),
            }
    
    return ContactMapResponse(
        markers=markers,
        total=len(markers),
        clustered=False,
        bounds=bounds,
    )


@router.get("/", response_model=ContactListResponse)
async def list_contacts(
    # Pagination
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    sort_by: str = Query("name", pattern="^(name|last_name|specialty|city|last_activity_date)$"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
    # Filters
    search: Optional[str] = Query(None),
    specialty: Optional[str] = Query(None),
    organization: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    geography: Optional[str] = Query(None),
    is_physician: Optional[bool] = Query(None),
    active: Optional[bool] = Query(True),
    panel_status: Optional[str] = Query(None),
    session: Session = Depends(db_session),
):
    """
    List contacts with filtering and pagination.
    
    Returns a paginated list of contacts with various filter options.
    """
    # Build base query
    query = select(SfContact)
    
    # Apply filters
    filters = []
    
    if search:
        search_pattern = f"%{search}%"
        filters.append(
            or_(
                SfContact.name.ilike(search_pattern),
                SfContact.first_name.ilike(search_pattern),
                SfContact.last_name.ilike(search_pattern),
                SfContact.email.ilike(search_pattern),
                SfContact.npi.ilike(search_pattern),
            )
        )
    
    if specialty:
        filters.append(SfContact.specialty == specialty)
    
    if organization:
        filters.append(SfContact.contact_account_name.ilike(f"%{organization}%"))
    
    if city:
        filters.append(SfContact.mailing_city == city)
    
    if state:
        filters.append(SfContact.mailing_state == state)
    
    if geography:
        filters.append(SfContact.geography == geography)
    
    if is_physician is not None:
        filters.append(SfContact.is_physician == is_physician)
    
    if active is not None:
        filters.append(SfContact.active == active)
    
    if panel_status:
        filters.append(SfContact.panel_status == panel_status)
    
    if filters:
        query = query.where(and_(*filters))
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = session.execute(count_query).scalar()
    
    # Apply sorting
    sort_column = getattr(SfContact, sort_by)
    if sort_order == "desc":
        sort_column = sort_column.desc()
    query = query.order_by(sort_column)
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    # Execute query
    contacts = session.execute(query).scalars().all()
    
    # Transform to response model
    items = [
        ContactListItem(
            id=str(contact.id),
            salesforce_id=contact.salesforce_id,
            name=contact.name,
            first_name=contact.first_name,
            last_name=contact.last_name,
            title=contact.title,
            email=contact.email,
            phone=contact.phone,
            specialty=contact.specialty,
            organization=contact.contact_account_name,
            mailing_address=contact.mailing_address_compound,
            city=contact.mailing_city,
            state=contact.mailing_state,
            is_physician=contact.is_physician,
            active=contact.active,
            last_activity_date=contact.last_activity_date,
        )
        for contact in contacts
    ]
    
    return ContactListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        has_more=(page * page_size) < total,
    )


@router.get("/{contact_id}", response_model=ContactDetail)
async def get_contact_detail(
    contact_id: str,
    session: Session = Depends(db_session),
):
    """
    Get detailed information for a specific contact.
    """
    query = select(SfContact).where(
        or_(
            SfContact.id == contact_id,
            SfContact.salesforce_id == contact_id,
        )
    )
    
    contact = session.execute(query).scalar_one_or_none()
    
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    return ContactDetail(
        id=str(contact.id),
        salesforce_id=contact.salesforce_id,
        first_name=contact.first_name,
        last_name=contact.last_name,
        middle_name=contact.middle_name,
        salutation=contact.salutation,
        suffix=contact.suffix,
        name=contact.name,
        full_name=contact.full_name,
        email=contact.email,
        phone=contact.phone,
        mobile_phone=contact.mobile_phone,
        fax=contact.fax,
        home_phone=contact.home_phone,
        other_phone=contact.other_phone,
        title=contact.title,
        mailing_street=contact.mailing_street,
        mailing_city=contact.mailing_city,
        mailing_state=contact.mailing_state,
        mailing_postal_code=contact.mailing_postal_code,
        mailing_country=contact.mailing_country,
        mailing_latitude=contact.mailing_latitude,
        mailing_longitude=contact.mailing_longitude,
        mailing_address_compound=contact.mailing_address_compound,
        specialty=contact.specialty,
        npi=contact.npi,
        is_physician=contact.is_physician,
        active=contact.active,
        contact_account_name=contact.contact_account_name,
        last_activity_date=contact.last_activity_date,
        days_since_last_visit=contact.days_since_last_visit,
        external_id=contact.external_id,
        epic_id=contact.epic_id,
        geography=contact.geography,
        primary_geography=contact.primary_geography,
        primary_mgma_specialty=contact.primary_mgma_specialty,
        network_picklist=contact.network_picklist,
        panel_status=contact.panel_status,
    )


@router.get("/filter-options", response_model=ContactFilterOptions)
async def get_filter_options(
    session: Session = Depends(db_session),
):
    """
    Get available filter options for contacts.
    
    Returns distinct values for various filter fields.
    """
    # Get distinct specialties
    specialty_query = (
        select(distinct(SfContact.specialty))
        .where(SfContact.specialty.isnot(None))
        .order_by(SfContact.specialty)
    )
    specialties = [s for s in session.execute(specialty_query).scalars().all() if s]
    
    # Get distinct organizations
    org_query = (
        select(distinct(SfContact.contact_account_name))
        .where(SfContact.contact_account_name.isnot(None))
        .order_by(SfContact.contact_account_name)
    )
    organizations = [o for o in session.execute(org_query).scalars().all() if o]
    
    # Get distinct cities
    city_query = (
        select(distinct(SfContact.mailing_city))
        .where(SfContact.mailing_city.isnot(None))
        .order_by(SfContact.mailing_city)
    )
    cities = [c for c in session.execute(city_query).scalars().all() if c]
    
    # Get distinct states
    state_query = (
        select(distinct(SfContact.mailing_state))
        .where(SfContact.mailing_state.isnot(None))
        .order_by(SfContact.mailing_state)
    )
    states = [s for s in session.execute(state_query).scalars().all() if s]
    
    # Get distinct geographies
    geo_query = (
        select(distinct(SfContact.geography))
        .where(SfContact.geography.isnot(None))
        .order_by(SfContact.geography)
    )
    geographies = [g for g in session.execute(geo_query).scalars().all() if g]
    
    # Get distinct panel statuses
    panel_query = (
        select(distinct(SfContact.panel_status))
        .where(SfContact.panel_status.isnot(None))
        .order_by(SfContact.panel_status)
    )
    panel_statuses = [p for p in session.execute(panel_query).scalars().all() if p]
    
    return ContactFilterOptions(
        specialties=specialties,
        organizations=organizations,
        cities=cities,
        states=states,
        geographies=geographies,
        panel_statuses=panel_statuses,
    )