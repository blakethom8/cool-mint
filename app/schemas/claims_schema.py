"""
Claims Data Schema Module

This module defines Pydantic schemas for the Market Explorer 2.0 claims data API.
It includes schemas for providers, sites of service, visits, and various API responses.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


# Base schemas for core entities
class ClaimsProviderBase(BaseModel):
    """Base schema for claims provider data"""
    npi: str = Field(..., description="National Provider Identifier")
    name: str = Field(..., description="Provider's full name")
    specialty: str = Field(..., description="Provider's primary medical specialty")
    geomarket: Optional[str] = Field(None, description="Geographic market area")
    provider_group: Optional[str] = Field(None, description="Provider group or organization")
    specialty_grandparent: Optional[str] = Field(None, description="High-level specialty category")
    service_line: Optional[str] = Field(None, description="Service line category")
    top_payer: Optional[str] = Field(None, description="Primary payer")
    top_payer_percent: Optional[float] = Field(None, description="Percentage from top payer")
    total_visits: int = Field(0, description="Total visits across all sites")


class ClaimsProviderDetail(ClaimsProviderBase):
    """Detailed claims provider schema with all fields"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(..., description="Unique provider identifier")
    top_referring_org: Optional[str] = Field(None, description="Top referring organization")
    top_sos_name: Optional[str] = Field(None, description="Primary site of service")
    top_sos_latitude: Optional[float] = Field(None, description="Primary site latitude")
    top_sos_longitude: Optional[float] = Field(None, description="Primary site longitude")
    top_sos_address: Optional[str] = Field(None, description="Primary site address")
    created_at: datetime = Field(..., description="Record creation timestamp")
    updated_at: datetime = Field(..., description="Record update timestamp")


class ClaimsProviderListItem(BaseModel):
    """Simplified provider schema for list views"""
    id: UUID = Field(..., description="Unique provider identifier")
    npi: str = Field(..., description="National Provider Identifier")
    name: str = Field(..., description="Provider's full name")
    specialty: str = Field(..., description="Provider's primary medical specialty")
    provider_group: Optional[str] = Field(None, description="Provider group")
    geomarket: Optional[str] = Field(None, description="Geographic market")
    total_visits: int = Field(0, description="Total visits")


class SiteOfServiceBase(BaseModel):
    """Base schema for site of service data"""
    name: str = Field(..., description="Site of service name")
    city: Optional[str] = Field(None, description="City location")
    county: Optional[str] = Field(None, description="County location")
    site_type: Optional[str] = Field(None, description="Type of facility")
    zip_code: Optional[str] = Field(None, description="ZIP code")
    latitude: Optional[float] = Field(None, description="Latitude coordinate")
    longitude: Optional[float] = Field(None, description="Longitude coordinate")
    geomarket: Optional[str] = Field(None, description="Geographic market area")
    address: Optional[str] = Field(None, description="Full address")


class SiteOfServiceDetail(SiteOfServiceBase):
    """Detailed site of service schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(..., description="Unique site identifier")
    legacy_id: str = Field(..., description="Legacy identifier for backward compatibility")
    created_at: datetime = Field(..., description="Record creation timestamp")
    updated_at: datetime = Field(..., description="Record update timestamp")


class SiteOfServiceListItem(BaseModel):
    """Simplified site schema for list views"""
    id: UUID = Field(..., description="Unique site identifier")
    name: str = Field(..., description="Site of service name")
    city: Optional[str] = Field(None, description="City location")
    site_type: Optional[str] = Field(None, description="Type of facility")
    geomarket: Optional[str] = Field(None, description="Geographic market")
    latitude: Optional[float] = Field(None, description="Latitude coordinate")
    longitude: Optional[float] = Field(None, description="Longitude coordinate")
    total_visits: Optional[int] = Field(0, description="Total visits at this site")
    provider_count: Optional[int] = Field(0, description="Number of providers at this site")


class ClaimsVisitBase(BaseModel):
    """Base schema for visit data"""
    visits: int = Field(..., description="Number of visits")
    has_oncology: bool = Field(False, description="Includes oncology services")
    has_surgery: bool = Field(False, description="Includes surgical services")  
    has_inpatient: bool = Field(False, description="Includes inpatient services")


class ClaimsVisitDetail(ClaimsVisitBase):
    """Detailed visit schema"""
    id: UUID = Field(..., description="Unique visit record identifier")
    provider_id: UUID = Field(..., description="Provider identifier")
    site_id: UUID = Field(..., description="Site identifier")
    created_at: datetime = Field(..., description="Record creation timestamp")


# Map marker schemas
class MapMarker(BaseModel):
    """Schema for map markers representing sites of service"""
    id: UUID = Field(..., description="Site identifier")
    name: str = Field(..., description="Site name")
    latitude: float = Field(..., description="Latitude coordinate")
    longitude: float = Field(..., description="Longitude coordinate")
    total_visits: int = Field(0, description="Total visits at this site")
    provider_count: int = Field(0, description="Number of providers")
    site_type: Optional[str] = Field(None, description="Type of facility")
    city: Optional[str] = Field(None, description="City location")
    geomarket: Optional[str] = Field(None, description="Geographic market")


class MapMarkersResponse(BaseModel):
    """Response schema for map markers endpoint"""
    markers: List[MapMarker] = Field(..., description="List of map markers")
    total_count: int = Field(..., description="Total number of markers")
    bounds: Optional[Dict[str, float]] = Field(None, description="Geographic bounds of markers")


# Provider group schemas
class ProviderGroup(BaseModel):
    """Schema for provider group aggregation"""
    name: str = Field(..., description="Provider group name")
    provider_count: int = Field(0, description="Number of providers in group")
    total_visits: int = Field(0, description="Total visits for group")
    specialties: List[str] = Field([], description="Specialties represented in group")
    geomarkets: List[str] = Field([], description="Geographic markets served")
    top_sites: List[str] = Field([], description="Top sites by volume")


# Filter schemas
class ClaimsFilters(BaseModel):
    """Schema for filtering claims data"""
    # Geographic filters
    geomarket: Optional[List[str]] = Field(None, description="Geographic markets")
    city: Optional[List[str]] = Field(None, description="Cities")
    county: Optional[List[str]] = Field(None, description="Counties")
    north: Optional[float] = Field(None, description="Northern boundary latitude")
    south: Optional[float] = Field(None, description="Southern boundary latitude")
    east: Optional[float] = Field(None, description="Eastern boundary longitude")
    west: Optional[float] = Field(None, description="Western boundary longitude")
    
    # Provider filters
    specialty: Optional[List[str]] = Field(None, description="Provider specialties")
    provider_group: Optional[List[str]] = Field(None, description="Provider groups")
    min_visits: Optional[int] = Field(None, description="Minimum visit count")
    max_visits: Optional[int] = Field(None, description="Maximum visit count")
    
    # Site filters
    site_type: Optional[List[str]] = Field(None, description="Site types")
    has_coordinates: Optional[bool] = Field(None, description="Only sites with lat/lng")
    
    # Service filters
    has_oncology: Optional[bool] = Field(None, description="Has oncology services")
    has_surgery: Optional[bool] = Field(None, description="Has surgical services")
    has_inpatient: Optional[bool] = Field(None, description="Has inpatient services")
    
    # Search
    search: Optional[str] = Field(None, description="Text search across names")


# Pagination schemas
class PaginationMeta(BaseModel):
    """Pagination metadata"""
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Items per page")
    total_items: int = Field(..., description="Total number of items")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Has next page")
    has_prev: bool = Field(..., description="Has previous page")


class ClaimsStatistics(BaseModel):
    """General statistics for claims data"""
    total_visits: int = Field(0, description="Total visits")
    total_providers: int = Field(0, description="Total providers")
    total_sites: int = Field(0, description="Total sites")
    average_visits_per_site: float = Field(0, description="Average visits per site")
    average_visits_per_provider: float = Field(0, description="Average visits per provider")


class ClaimsProvidersResponse(BaseModel):
    """Response schema for providers list endpoint"""
    items: List[ClaimsProviderListItem] = Field(..., description="List of providers")
    meta: PaginationMeta = Field(..., description="Pagination metadata")
    statistics: Optional[ClaimsStatistics] = Field(None, description="Optional statistics")


class SitesOfServiceResponse(BaseModel):
    """Response schema for sites list endpoint"""
    items: List[SiteOfServiceListItem] = Field(..., description="List of sites")
    meta: PaginationMeta = Field(..., description="Pagination metadata")
    statistics: Optional[ClaimsStatistics] = Field(None, description="Optional statistics")


class ProviderGroupsResponse(BaseModel):
    """Response schema for provider groups endpoint"""
    items: List[ProviderGroup] = Field(..., description="List of provider groups")
    meta: PaginationMeta = Field(..., description="Pagination metadata")
    statistics: Optional[ClaimsStatistics] = Field(None, description="Optional statistics")


# Statistics schemas
class VisitStatistics(BaseModel):
    """Visit statistics for a provider or site"""
    total_visits: int = Field(0, description="Total visits")
    oncology_visits: int = Field(0, description="Oncology visits")
    surgery_visits: int = Field(0, description="Surgery visits")
    inpatient_visits: int = Field(0, description="Inpatient visits")
    outpatient_visits: int = Field(0, description="Outpatient visits")


class SiteStatistics(BaseModel):
    """Statistics for a site of service"""
    site_id: UUID = Field(..., description="Site identifier")
    visit_stats: VisitStatistics = Field(..., description="Visit statistics")
    provider_count: int = Field(0, description="Number of providers")
    top_specialties: List[Dict[str, Any]] = Field([], description="Top specialties by volume")
    top_providers: List[Dict[str, Any]] = Field([], description="Top providers by volume")


class ProviderStatistics(BaseModel):
    """Statistics for a provider"""
    provider_id: UUID = Field(..., description="Provider identifier")
    visit_stats: VisitStatistics = Field(..., description="Visit statistics")
    site_count: int = Field(0, description="Number of sites")
    top_sites: List[Dict[str, Any]] = Field([], description="Top sites by volume")


# Notes and classification schemas (for future use)
class MarketNoteBase(BaseModel):
    """Base schema for market notes"""
    note_type: str = Field("general", description="Type of note")
    title: Optional[str] = Field(None, description="Note title")
    content: str = Field(..., description="Note content")
    tags: Optional[List[str]] = Field(None, description="Note tags")


class MarketNote(MarketNoteBase):
    """Market note with metadata"""
    id: UUID = Field(..., description="Note identifier")
    provider_id: Optional[UUID] = Field(None, description="Related provider")
    site_id: Optional[UUID] = Field(None, description="Related site")
    provider_group: Optional[str] = Field(None, description="Related provider group")
    author: Optional[str] = Field(None, description="Note author")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Update timestamp")


class LeadClassificationBase(BaseModel):
    """Base schema for lead classifications"""
    classification: str = Field(..., description="Classification type")
    confidence_score: Optional[int] = Field(None, description="Confidence score 1-10")
    reason: Optional[str] = Field(None, description="Classification reasoning")


class LeadClassification(LeadClassificationBase):
    """Lead classification with metadata"""
    id: UUID = Field(..., description="Classification identifier")
    provider_id: Optional[UUID] = Field(None, description="Related provider")
    site_id: Optional[UUID] = Field(None, description="Related site")
    provider_group: Optional[str] = Field(None, description="Related provider group")
    classified_by: Optional[str] = Field(None, description="Classifier")
    created_at: datetime = Field(..., description="Creation timestamp")


# Filter options schemas
class FilterOptions(BaseModel):
    """Available filter options"""
    geomarkets: List[str] = Field([], description="Available geomarkets")
    cities: List[str] = Field([], description="Available cities")
    counties: List[str] = Field([], description="Available counties")
    specialties: List[str] = Field([], description="Available specialties")
    provider_groups: List[str] = Field([], description="Available provider groups")
    site_types: List[str] = Field([], description="Available site types")
    specialty_grandparents: List[str] = Field([], description="Available specialty categories")
    service_lines: List[str] = Field([], description="Available service lines")