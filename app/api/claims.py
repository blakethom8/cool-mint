"""
Claims Data API Module

This module provides FastAPI endpoints for the Market Explorer 2.0 claims data.
It includes endpoints for providers, sites of service, visits, and map data.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, distinct

from database.session import db_session
from database.data_models.claims_data import ClaimsProvider, SiteOfService, ClaimsVisit
from schemas.claims_schema import (
    ClaimsProviderDetail,
    ClaimsProviderListItem,
    ClaimsProvidersResponse,
    SiteOfServiceDetail,
    SiteOfServiceListItem,
    SitesOfServiceResponse,
    ProviderGroup,
    ProviderGroupsResponse,
    MapMarker,
    MapMarkersResponse,
    ClaimsFilters,
    PaginationMeta,
    FilterOptions,
    SiteStatistics,
    ProviderStatistics,
    VisitStatistics,
    ClaimsStatistics
)

router = APIRouter(prefix="/claims", tags=["claims"])


def apply_filters(query, filters: ClaimsFilters, model_class):
    """Apply filters to a SQLAlchemy query"""
    
    # Geographic filters
    if filters.geomarket:
        query = query.filter(model_class.geomarket.in_(filters.geomarket))
    
    if filters.city and hasattr(model_class, 'city'):
        query = query.filter(model_class.city.in_(filters.city))
    
    if filters.county and hasattr(model_class, 'county'):
        query = query.filter(model_class.county.in_(filters.county))
    
    # Bounding box filter for sites with coordinates
    if filters.north and filters.south and filters.east and filters.west:
        if hasattr(model_class, 'latitude') and hasattr(model_class, 'longitude'):
            query = query.filter(
                and_(
                    model_class.latitude.between(filters.south, filters.north),
                    model_class.longitude.between(filters.west, filters.east)
                )
            )
    
    # Provider-specific filters
    if hasattr(model_class, 'specialty') and filters.specialty:
        query = query.filter(model_class.specialty.in_(filters.specialty))
    
    if hasattr(model_class, 'provider_group') and filters.provider_group:
        query = query.filter(model_class.provider_group.in_(filters.provider_group))
    
    # Site-specific filters
    if hasattr(model_class, 'site_type') and filters.site_type:
        query = query.filter(model_class.site_type.in_(filters.site_type))
    
    # Coordinate filter
    if filters.has_coordinates and hasattr(model_class, 'latitude'):
        query = query.filter(
            and_(
                model_class.latitude.isnot(None),
                model_class.longitude.isnot(None)
            )
        )
    
    # Search filter
    if filters.search:
        if hasattr(model_class, 'name'):
            query = query.filter(model_class.name.ilike(f"%{filters.search}%"))
    
    return query


@router.get("/providers", response_model=ClaimsProvidersResponse)
async def get_providers(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=200, description="Items per page"),
    geomarket: Optional[List[str]] = Query(None, description="Filter by geomarket"),
    specialty: Optional[List[str]] = Query(None, description="Filter by specialty"),
    provider_group: Optional[List[str]] = Query(None, description="Filter by provider group"),
    min_visits: Optional[int] = Query(None, ge=0, description="Minimum visit count"),
    max_visits: Optional[int] = Query(None, ge=0, description="Maximum visit count"),
    search: Optional[str] = Query(None, description="Search by provider name"),
    session: Session = Depends(db_session)
):
    """Get list of providers with filtering and pagination"""
    
    # Create filters object
    filters = ClaimsFilters(
        geomarket=geomarket,
        specialty=specialty,
        provider_group=provider_group,
        min_visits=min_visits,
        max_visits=max_visits,
        search=search
    )
    
    # Base query
    query = session.query(ClaimsProvider)
    
    # Apply filters
    query = apply_filters(query, filters, ClaimsProvider)
    
    # Visit count filters
    if filters.min_visits is not None:
        query = query.filter(ClaimsProvider.total_visits >= filters.min_visits)
    
    if filters.max_visits is not None:
        query = query.filter(ClaimsProvider.total_visits <= filters.max_visits)
    
    # Get total count
    total_count = query.count()
    
    # Apply pagination
    offset = (page - 1) * per_page
    providers = query.offset(offset).limit(per_page).all()
    
    # Create response
    items = [
        ClaimsProviderListItem(
            id=p.id,
            npi=p.npi,
            name=p.name,
            specialty=p.specialty,
            provider_group=p.provider_group,
            geomarket=p.geomarket,
            total_visits=p.total_visits
        )
        for p in providers
    ]
    
    meta = PaginationMeta(
        page=page,
        per_page=per_page,
        total_items=total_count,
        total_pages=(total_count + per_page - 1) // per_page,
        has_next=page * per_page < total_count,
        has_prev=page > 1
    )
    
    # Calculate statistics
    stats_query = session.query(
        func.sum(ClaimsProvider.total_visits).label('total_visits'),
        func.count(distinct(ClaimsProvider.id)).label('total_providers')
    )
    stats_query = apply_filters(stats_query, filters, ClaimsProvider)
    stats = stats_query.first()
    
    total_sites = session.query(func.count(distinct(SiteOfService.id))).scalar() or 0
    
    statistics = ClaimsStatistics(
        total_visits=int(stats.total_visits or 0),
        total_providers=int(stats.total_providers or 0),
        total_sites=total_sites,
        average_visits_per_site=float(stats.total_visits or 0) / total_sites if total_sites > 0 else 0,
        average_visits_per_provider=float(stats.total_visits or 0) / int(stats.total_providers or 1)
    )
    
    return ClaimsProvidersResponse(items=items, meta=meta, statistics=statistics)


@router.get("/providers/{provider_id}", response_model=ClaimsProviderDetail)
async def get_provider(
    provider_id: UUID,
    session: Session = Depends(db_session)
):
    """Get detailed information for a specific provider"""
    
    provider = session.query(ClaimsProvider).filter(ClaimsProvider.id == provider_id).first()
    
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    return ClaimsProviderDetail.from_orm(provider)


@router.get("/sites", response_model=SitesOfServiceResponse)
async def get_sites(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=200, description="Items per page"),
    geomarket: Optional[List[str]] = Query(None, description="Filter by geomarket"),
    city: Optional[List[str]] = Query(None, description="Filter by city"),
    county: Optional[List[str]] = Query(None, description="Filter by county"),
    site_type: Optional[List[str]] = Query(None, description="Filter by site type"),
    has_coordinates: Optional[bool] = Query(None, description="Only sites with coordinates"),
    north: Optional[float] = Query(None, description="Northern boundary"),
    south: Optional[float] = Query(None, description="Southern boundary"),
    east: Optional[float] = Query(None, description="Eastern boundary"),
    west: Optional[float] = Query(None, description="Western boundary"),
    search: Optional[str] = Query(None, description="Search by site name"),
    session: Session = Depends(db_session)
):
    """Get list of sites of service with filtering and pagination"""
    
    # Create filters object
    filters = ClaimsFilters(
        geomarket=geomarket,
        city=city,
        county=county,
        site_type=site_type,
        has_coordinates=has_coordinates,
        north=north,
        south=south,
        east=east,
        west=west,
        search=search
    )
    
    # Base query with visit aggregation
    query = session.query(
        SiteOfService,
        func.coalesce(func.sum(ClaimsVisit.visits), 0).label('total_visits'),
        func.count(distinct(ClaimsVisit.provider_id)).label('provider_count')
    ).outerjoin(ClaimsVisit)
    
    # Apply filters
    query = apply_filters(query, filters, SiteOfService)
    
    # Group by site
    query = query.group_by(SiteOfService.id)
    
    # Get total count
    total_count = query.count()
    
    # Apply pagination
    offset = (page - 1) * per_page
    results = query.offset(offset).limit(per_page).all()
    
    # Create response
    items = [
        SiteOfServiceListItem(
            id=site.id,
            name=site.name,
            city=site.city,
            site_type=site.site_type,
            geomarket=site.geomarket,
            latitude=site.latitude,
            longitude=site.longitude,
            total_visits=int(total_visits or 0),
            provider_count=int(provider_count or 0)
        )
        for site, total_visits, provider_count in results
    ]
    
    meta = PaginationMeta(
        page=page,
        per_page=per_page,
        total_items=total_count,
        total_pages=(total_count + per_page - 1) // per_page,
        has_next=page * per_page < total_count,
        has_prev=page > 1
    )
    
    # Calculate statistics for filtered data
    stats_query = session.query(
        func.sum(ClaimsVisit.visits).label('total_visits'),
        func.count(distinct(ClaimsVisit.provider_id)).label('total_providers'),
        func.count(distinct(ClaimsVisit.site_id)).label('total_sites')
    ).join(SiteOfService)
    
    # Apply same filters
    stats_query = apply_filters(stats_query, filters, SiteOfService)
    stats = stats_query.first()
    
    statistics = ClaimsStatistics(
        total_visits=int(stats.total_visits or 0),
        total_providers=int(stats.total_providers or 0),
        total_sites=int(stats.total_sites or 0),
        average_visits_per_site=float(stats.total_visits or 0) / int(stats.total_sites or 1),
        average_visits_per_provider=float(stats.total_visits or 0) / int(stats.total_providers or 1)
    )
    
    return SitesOfServiceResponse(items=items, meta=meta, statistics=statistics)


@router.get("/sites/{site_id}", response_model=SiteOfServiceDetail)
async def get_site(
    site_id: UUID,
    session: Session = Depends(db_session)
):
    """Get detailed information for a specific site of service"""
    
    site = session.query(SiteOfService).filter(SiteOfService.id == site_id).first()
    
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    
    return SiteOfServiceDetail.from_orm(site)


@router.get("/map-markers", response_model=MapMarkersResponse)
async def get_map_markers(
    geomarket: Optional[List[str]] = Query(None, description="Filter by geomarket"),
    city: Optional[List[str]] = Query(None, description="Filter by city"),
    site_type: Optional[List[str]] = Query(None, description="Filter by site type"),
    north: Optional[float] = Query(None, description="Northern boundary"),
    south: Optional[float] = Query(None, description="Southern boundary"),
    east: Optional[float] = Query(None, description="Eastern boundary"),
    west: Optional[float] = Query(None, description="Western boundary"),
    min_visits: Optional[int] = Query(None, ge=0, description="Minimum visit count"),
    has_oncology: Optional[bool] = Query(None, description="Has oncology services"),
    has_surgery: Optional[bool] = Query(None, description="Has surgical services"),
    has_inpatient: Optional[bool] = Query(None, description="Has inpatient services"),
    session: Session = Depends(db_session)
):
    """Get optimized map markers for sites of service"""
    
    # Create filters object
    filters = ClaimsFilters(
        geomarket=geomarket,
        city=city,
        site_type=site_type,
        north=north,
        south=south,
        east=east,
        west=west,
        min_visits=min_visits,
        has_oncology=has_oncology,
        has_surgery=has_surgery,
        has_inpatient=has_inpatient,
        has_coordinates=True  # Only show sites with coordinates on map
    )
    
    # Query with visit aggregation and service flags
    query = session.query(
        SiteOfService.id,
        SiteOfService.name,
        SiteOfService.latitude,
        SiteOfService.longitude,
        SiteOfService.site_type,
        SiteOfService.city,
        SiteOfService.geomarket,
        func.coalesce(func.sum(ClaimsVisit.visits), 0).label('total_visits'),
        func.count(distinct(ClaimsVisit.provider_id)).label('provider_count'),
        func.bool_or(ClaimsVisit.has_oncology).label('site_has_oncology'),
        func.bool_or(ClaimsVisit.has_surgery).label('site_has_surgery'),
        func.bool_or(ClaimsVisit.has_inpatient).label('site_has_inpatient')
    ).outerjoin(ClaimsVisit)
    
    # Apply basic filters
    query = apply_filters(query, filters, SiteOfService)
    
    # Group by site
    query = query.group_by(
        SiteOfService.id,
        SiteOfService.name,
        SiteOfService.latitude,
        SiteOfService.longitude,
        SiteOfService.site_type,
        SiteOfService.city,
        SiteOfService.geomarket
    )
    
    # Apply service filters
    if filters.has_oncology:
        query = query.having(func.bool_or(ClaimsVisit.has_oncology) == True)
    
    if filters.has_surgery:
        query = query.having(func.bool_or(ClaimsVisit.has_surgery) == True)
    
    if filters.has_inpatient:
        query = query.having(func.bool_or(ClaimsVisit.has_inpatient) == True)
    
    # Apply visit count filter
    if filters.min_visits:
        query = query.having(func.sum(ClaimsVisit.visits) >= filters.min_visits)
    
    # Execute query
    results = query.all()
    
    # Create markers
    markers = [
        MapMarker(
            id=site_id,
            name=name,
            latitude=latitude,
            longitude=longitude,
            total_visits=int(total_visits or 0),
            provider_count=int(provider_count or 0),
            site_type=site_type,
            city=city,
            geomarket=geomarket
        )
        for (site_id, name, latitude, longitude, site_type, city, geomarket,
             total_visits, provider_count, _, _, _) in results
        if latitude is not None and longitude is not None
    ]
    
    # Calculate bounds
    bounds = None
    if markers:
        lats = [m.latitude for m in markers]
        lngs = [m.longitude for m in markers]
        bounds = {
            "north": max(lats),
            "south": min(lats),
            "east": max(lngs),
            "west": min(lngs)
        }
    
    return MapMarkersResponse(
        markers=markers,
        total_count=len(markers),
        bounds=bounds
    )


@router.get("/provider-groups", response_model=ProviderGroupsResponse)
async def get_provider_groups(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=200, description="Items per page"),
    geomarket: Optional[List[str]] = Query(None, description="Filter by geomarket"),
    specialty: Optional[List[str]] = Query(None, description="Filter by specialty"),
    min_providers: Optional[int] = Query(None, ge=1, description="Minimum provider count"),
    min_visits: Optional[int] = Query(None, ge=0, description="Minimum total visits"),
    search: Optional[str] = Query(None, description="Search by group name"),
    session: Session = Depends(db_session)
):
    """Get aggregated provider group data"""
    
    # Base query
    query = session.query(
        ClaimsProvider.provider_group,
        func.count(ClaimsProvider.id).label('provider_count'),
        func.sum(ClaimsProvider.total_visits).label('total_visits'),
        func.array_agg(distinct(ClaimsProvider.specialty)).label('specialties'),
        func.array_agg(distinct(ClaimsProvider.geomarket)).label('geomarkets')
    ).filter(ClaimsProvider.provider_group.isnot(None))
    
    # Apply filters
    if geomarket:
        query = query.filter(ClaimsProvider.geomarket.in_(geomarket))
    
    if specialty:
        query = query.filter(ClaimsProvider.specialty.in_(specialty))
    
    if search:
        query = query.filter(ClaimsProvider.provider_group.ilike(f"%{search}%"))
    
    # Group by provider group
    query = query.group_by(ClaimsProvider.provider_group)
    
    # Apply aggregation filters
    if min_providers:
        query = query.having(func.count(ClaimsProvider.id) >= min_providers)
    
    if min_visits:
        query = query.having(func.sum(ClaimsProvider.total_visits) >= min_visits)
    
    # Order by total visits
    query = query.order_by(func.sum(ClaimsProvider.total_visits).desc())
    
    # Get total count
    total_count = query.count()
    
    # Apply pagination
    offset = (page - 1) * per_page
    results = query.offset(offset).limit(per_page).all()
    
    # Create response
    items = [
        ProviderGroup(
            name=group_name or "Unknown",
            provider_count=int(provider_count),
            total_visits=int(total_visits or 0),
            specialties=[s for s in (specialties or []) if s],
            geomarkets=[g for g in (geomarkets or []) if g],
            top_sites=[]  # TODO: Add top sites query
        )
        for (group_name, provider_count, total_visits, specialties, geomarkets) in results
    ]
    
    meta = PaginationMeta(
        page=page,
        per_page=per_page,
        total_items=total_count,
        total_pages=(total_count + per_page - 1) // per_page,
        has_next=page * per_page < total_count,
        has_prev=page > 1
    )
    
    # Calculate overall statistics
    total_visits = sum(item.total_visits for item in items)
    total_providers = sum(item.provider_count for item in items)
    total_sites = session.query(func.count(distinct(SiteOfService.id))).scalar() or 0
    
    statistics = ClaimsStatistics(
        total_visits=total_visits,
        total_providers=total_providers,
        total_sites=total_sites,
        average_visits_per_site=float(total_visits) / total_sites if total_sites > 0 else 0,
        average_visits_per_provider=float(total_visits) / total_providers if total_providers > 0 else 0
    )
    
    return ProviderGroupsResponse(items=items, meta=meta, statistics=statistics)


@router.get("/filter-options", response_model=FilterOptions)
async def get_filter_options(session: Session = Depends(db_session)):
    """Get available filter options for dropdowns"""
    
    # Get distinct values for filters
    geomarkets = session.query(distinct(ClaimsProvider.geomarket)).filter(
        ClaimsProvider.geomarket.isnot(None)
    ).order_by(ClaimsProvider.geomarket).all()
    
    specialties = session.query(distinct(ClaimsProvider.specialty)).filter(
        ClaimsProvider.specialty.isnot(None)
    ).order_by(ClaimsProvider.specialty).all()
    
    provider_groups = session.query(distinct(ClaimsProvider.provider_group)).filter(
        ClaimsProvider.provider_group.isnot(None)
    ).order_by(ClaimsProvider.provider_group).all()
    
    cities = session.query(distinct(SiteOfService.city)).filter(
        SiteOfService.city.isnot(None)
    ).order_by(SiteOfService.city).all()
    
    counties = session.query(distinct(SiteOfService.county)).filter(
        SiteOfService.county.isnot(None)
    ).order_by(SiteOfService.county).all()
    
    site_types = session.query(distinct(SiteOfService.site_type)).filter(
        SiteOfService.site_type.isnot(None)
    ).order_by(SiteOfService.site_type).all()
    
    specialty_grandparents = session.query(distinct(ClaimsProvider.specialty_grandparent)).filter(
        ClaimsProvider.specialty_grandparent.isnot(None)
    ).order_by(ClaimsProvider.specialty_grandparent).all()
    
    service_lines = session.query(distinct(ClaimsProvider.service_line)).filter(
        ClaimsProvider.service_line.isnot(None)
    ).order_by(ClaimsProvider.service_line).all()
    
    return FilterOptions(
        geomarkets=[g[0] for g in geomarkets],
        cities=[c[0] for c in cities],
        counties=[c[0] for c in counties],
        specialties=[s[0] for s in specialties],
        provider_groups=[p[0] for p in provider_groups],
        site_types=[t[0] for t in site_types],
        specialty_grandparents=[s[0] for s in specialty_grandparents],
        service_lines=[s[0] for s in service_lines]
    )


@router.get("/sites/{site_id}/statistics", response_model=SiteStatistics)
async def get_site_statistics(
    site_id: UUID,
    session: Session = Depends(db_session)
):
    """Get detailed statistics for a specific site"""
    
    # Verify site exists
    site = session.query(SiteOfService).filter(SiteOfService.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    
    # Get visit statistics
    visit_stats = session.query(
        func.sum(ClaimsVisit.visits).label('total_visits'),
        func.sum(func.case([(ClaimsVisit.has_oncology, ClaimsVisit.visits)], else_=0)).label('oncology_visits'),
        func.sum(func.case([(ClaimsVisit.has_surgery, ClaimsVisit.visits)], else_=0)).label('surgery_visits'),
        func.sum(func.case([(ClaimsVisit.has_inpatient, ClaimsVisit.visits)], else_=0)).label('inpatient_visits')
    ).filter(ClaimsVisit.site_id == site_id).first()
    
    # Get provider count
    provider_count = session.query(func.count(distinct(ClaimsVisit.provider_id))).filter(
        ClaimsVisit.site_id == site_id
    ).scalar() or 0
    
    # Get top specialties
    top_specialties = session.query(
        ClaimsProvider.specialty,
        func.sum(ClaimsVisit.visits).label('visits')
    ).join(ClaimsVisit).filter(
        ClaimsVisit.site_id == site_id
    ).group_by(ClaimsProvider.specialty).order_by(
        func.sum(ClaimsVisit.visits).desc()
    ).limit(5).all()
    
    # Get top providers
    top_providers = session.query(
        ClaimsProvider.name,
        ClaimsProvider.specialty,
        func.sum(ClaimsVisit.visits).label('visits')
    ).join(ClaimsVisit).filter(
        ClaimsVisit.site_id == site_id
    ).group_by(ClaimsProvider.id, ClaimsProvider.name, ClaimsProvider.specialty).order_by(
        func.sum(ClaimsVisit.visits).desc()
    ).limit(10).all()
    
    return SiteStatistics(
        site_id=site_id,
        visit_stats=VisitStatistics(
            total_visits=int(visit_stats.total_visits or 0),
            oncology_visits=int(visit_stats.oncology_visits or 0),
            surgery_visits=int(visit_stats.surgery_visits or 0),
            inpatient_visits=int(visit_stats.inpatient_visits or 0),
            outpatient_visits=int((visit_stats.total_visits or 0) - (visit_stats.inpatient_visits or 0))
        ),
        provider_count=provider_count,
        top_specialties=[
            {"specialty": specialty, "visits": int(visits)}
            for specialty, visits in top_specialties
        ],
        top_providers=[
            {"name": name, "specialty": specialty, "visits": int(visits)}
            for name, specialty, visits in top_providers
        ]
    )


@router.get("/providers/{provider_id}/statistics", response_model=ProviderStatistics)
async def get_provider_statistics(
    provider_id: UUID,
    session: Session = Depends(db_session)
):
    """Get detailed statistics for a specific provider"""
    
    # Verify provider exists
    provider = session.query(ClaimsProvider).filter(ClaimsProvider.id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    # Get visit statistics
    visit_stats = session.query(
        func.sum(ClaimsVisit.visits).label('total_visits'),
        func.sum(func.case([(ClaimsVisit.has_oncology, ClaimsVisit.visits)], else_=0)).label('oncology_visits'),
        func.sum(func.case([(ClaimsVisit.has_surgery, ClaimsVisit.visits)], else_=0)).label('surgery_visits'),
        func.sum(func.case([(ClaimsVisit.has_inpatient, ClaimsVisit.visits)], else_=0)).label('inpatient_visits')
    ).filter(ClaimsVisit.provider_id == provider_id).first()
    
    # Get site count
    site_count = session.query(func.count(distinct(ClaimsVisit.site_id))).filter(
        ClaimsVisit.provider_id == provider_id
    ).scalar() or 0
    
    # Get top sites
    top_sites = session.query(
        SiteOfService.name,
        SiteOfService.city,
        func.sum(ClaimsVisit.visits).label('visits')
    ).join(ClaimsVisit).filter(
        ClaimsVisit.provider_id == provider_id
    ).group_by(SiteOfService.id, SiteOfService.name, SiteOfService.city).order_by(
        func.sum(ClaimsVisit.visits).desc()
    ).limit(10).all()
    
    return ProviderStatistics(
        provider_id=provider_id,
        visit_stats=VisitStatistics(
            total_visits=int(visit_stats.total_visits or 0),
            oncology_visits=int(visit_stats.oncology_visits or 0),
            surgery_visits=int(visit_stats.surgery_visits or 0),
            inpatient_visits=int(visit_stats.inpatient_visits or 0),
            outpatient_visits=int((visit_stats.total_visits or 0) - (visit_stats.inpatient_visits or 0))
        ),
        site_count=site_count,
        top_sites=[
            {"name": name, "city": city, "visits": int(visits)}
            for name, city, visits in top_sites
        ]
    )


@router.get("/sites/{site_id}/providers", response_model=ClaimsProvidersResponse)
async def get_site_providers(
    site_id: UUID,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    session: Session = Depends(db_session),
):
    """Get all providers for a specific site (unfiltered)"""
    
    # First verify the site exists
    site = session.query(SiteOfService).filter(SiteOfService.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    
    # Get all visits for this site
    visits_query = session.query(ClaimsVisit).filter(ClaimsVisit.site_id == site_id)
    
    # Get unique provider IDs
    provider_ids = [visit.provider_id for visit in visits_query.all()]
    unique_provider_ids = list(set(provider_ids))
    
    # Get provider details
    providers_query = session.query(ClaimsProvider).filter(
        ClaimsProvider.id.in_(unique_provider_ids)
    ).order_by(ClaimsProvider.name)
    
    # Pagination
    total = providers_query.count()
    providers = providers_query.offset((page - 1) * per_page).limit(per_page).all()
    
    items = []
    for provider in providers:
        # Get visit count for this provider at this site
        visit_count = session.query(func.sum(ClaimsVisit.visits)).filter(
            ClaimsVisit.provider_id == provider.id,
            ClaimsVisit.site_id == site_id
        ).scalar() or 0
        
        items.append(ClaimsProviderListItem(
            id=provider.id,
            npi=provider.npi,
            name=provider.name,
            specialty=provider.specialty,
            provider_group=provider.provider_group,
            geomarket=provider.geomarket,
            city=site.city,  # Use site's city
            total_visits=visit_count
        ))
    
    meta = PaginationMeta(
        page=page,
        per_page=per_page,
        total_items=total,
        total_pages=(total + per_page - 1) // per_page,
        has_next=page * per_page < total,
        has_prev=page > 1
    )
    
    return ClaimsProvidersResponse(items=items, meta=meta)


@router.get("/sites/{site_id}/provider-groups", response_model=ProviderGroupsResponse)
async def get_site_provider_groups(
    site_id: UUID,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    session: Session = Depends(db_session),
):
    """Get provider groups for a specific site"""
    
    # First verify the site exists
    site = session.query(SiteOfService).filter(SiteOfService.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    
    # Get provider groups that have providers at this site
    groups_query = session.query(
        ClaimsProvider.provider_group,
        func.count(distinct(ClaimsProvider.id)).label('provider_count'),
        func.sum(ClaimsVisit.visits).label('total_visits'),
        func.array_agg(distinct(ClaimsProvider.specialty)).label('specialties'),
        func.array_agg(distinct(ClaimsProvider.geomarket)).label('geomarkets')
    ).join(
        ClaimsVisit,
        and_(
            ClaimsVisit.provider_id == ClaimsProvider.id,
            ClaimsVisit.site_id == site_id
        )
    ).filter(
        ClaimsProvider.provider_group.isnot(None)
    ).group_by(
        ClaimsProvider.provider_group
    ).order_by(
        func.sum(ClaimsVisit.visits).desc()
    )
    
    # Get total count
    total_count = groups_query.count()
    
    # Apply pagination
    offset = (page - 1) * per_page
    results = groups_query.offset(offset).limit(per_page).all()
    
    # Create response
    items = [
        ProviderGroup(
            name=group_name or "Unknown",
            provider_count=int(provider_count),
            total_visits=int(total_visits or 0),
            specialties=[s for s in (specialties or []) if s],
            geomarkets=[g for g in (geomarkets or []) if g],
            top_sites=[site.name]  # Include the current site
        )
        for (group_name, provider_count, total_visits, specialties, geomarkets) in results
    ]
    
    meta = PaginationMeta(
        page=page,
        per_page=per_page,
        total_items=total_count,
        total_pages=(total_count + per_page - 1) // per_page,
        has_next=page * per_page < total_count,
        has_prev=page > 1
    )
    
    # Calculate statistics for this site's provider groups
    total_visits = sum(item.total_visits for item in items)
    total_providers = sum(item.provider_count for item in items)
    
    statistics = ClaimsStatistics(
        total_visits=total_visits,
        total_providers=total_providers,
        total_sites=1,  # Just this site
        average_visits_per_site=float(total_visits),
        average_visits_per_provider=float(total_visits) / total_providers if total_providers > 0 else 0
    )
    
    return ProviderGroupsResponse(items=items, meta=meta, statistics=statistics)


@router.get("/sites/{site_id}/site-details", response_model=SitesOfServiceResponse)
async def get_site_quick_view(
    site_id: UUID,
    session: Session = Depends(db_session),
):
    """Get a single site for Quick View in Sites mode"""
    
    # Get the site with aggregated visit data
    result = session.query(
        SiteOfService,
        func.coalesce(func.sum(ClaimsVisit.visits), 0).label('total_visits'),
        func.count(distinct(ClaimsVisit.provider_id)).label('provider_count')
    ).outerjoin(ClaimsVisit).filter(
        SiteOfService.id == site_id
    ).group_by(SiteOfService.id).first()
    
    if not result:
        raise HTTPException(status_code=404, detail="Site not found")
    
    site, total_visits, provider_count = result
    
    # Create a single-item response
    item = SiteOfServiceListItem(
        id=site.id,
        name=site.name,
        city=site.city,
        site_type=site.site_type,
        geomarket=site.geomarket,
        latitude=site.latitude,
        longitude=site.longitude,
        total_visits=int(total_visits or 0),
        provider_count=int(provider_count or 0)
    )
    
    meta = PaginationMeta(
        page=1,
        per_page=1,
        total_items=1,
        total_pages=1,
        has_next=False,
        has_prev=False
    )
    
    # Calculate statistics for this single site
    statistics = ClaimsStatistics(
        total_visits=int(total_visits or 0),
        total_providers=int(provider_count or 0),
        total_sites=1,
        average_visits_per_site=float(total_visits or 0),
        average_visits_per_provider=float(total_visits or 0) / int(provider_count) if provider_count > 0 else 0
    )
    
    return SitesOfServiceResponse(items=[item], meta=meta, statistics=statistics)