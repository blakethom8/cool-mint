"""
Pydantic schemas for Relationship Management API.

These schemas define the data structures for the relationship management
endpoints, ensuring type safety and validation.
"""

from datetime import datetime, date
from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


# Base schemas
class RelationshipStatusInfo(BaseModel):
    """Status information with display details."""
    id: int
    code: str
    display_name: str
    

class LoyaltyStatusInfo(BaseModel):
    """Loyalty status information with display details."""
    id: int
    code: str
    display_name: str
    color_hex: Optional[str] = None


class EntityTypeInfo(BaseModel):
    """Entity type information."""
    id: int
    code: str
    common_name: str


# List/Table schemas
class RelationshipListItem(BaseModel):
    """Schema for relationship items in list view."""
    model_config = ConfigDict(from_attributes=True)
    
    relationship_id: UUID
    user_id: int
    user_name: str
    entity_type: EntityTypeInfo
    linked_entity_id: UUID
    entity_name: str
    entity_details: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional entity details (specialty, location, etc.)"
    )
    relationship_status: RelationshipStatusInfo
    loyalty_status: Optional[LoyaltyStatusInfo] = None
    lead_score: Optional[int] = Field(None, ge=1, le=5)
    last_activity_date: Optional[datetime] = None
    days_since_activity: Optional[int] = None
    engagement_frequency: Optional[str] = None
    activity_count: int = 0
    campaign_count: int = 0
    next_steps: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class RelationshipListResponse(BaseModel):
    """Response for relationship list endpoint."""
    items: List[RelationshipListItem]
    total_count: int
    page: int
    page_size: int
    total_pages: int


# Detail schemas
class ActivityLogItem(BaseModel):
    """Activity history item for relationship timeline."""
    activity_id: UUID
    activity_date: date
    subject: str
    description: Optional[str] = None
    activity_type: str
    mno_type: Optional[str] = None
    mno_subtype: Optional[str] = None
    status: str
    owner_name: str
    contact_names: List[str] = Field(default_factory=list)
    

class RelationshipMetrics(BaseModel):
    """Aggregated metrics for a relationship."""
    total_activities: int
    activities_last_30_days: int
    activities_last_90_days: int
    average_days_between_activities: Optional[float] = None
    most_common_activity_type: Optional[str] = None
    last_activity_days_ago: Optional[int] = None
    referral_count: int = 0
    meeting_count: int = 0
    call_count: int = 0
    email_count: int = 0


class CampaignInfo(BaseModel):
    """Campaign associated with relationship."""
    campaign_id: UUID
    campaign_name: str
    status: str
    start_date: date
    end_date: Optional[date] = None


class RelationshipDetail(BaseModel):
    """Detailed relationship information."""
    model_config = ConfigDict(from_attributes=True)
    
    # Core fields
    relationship_id: UUID
    user_id: int
    user_name: str
    user_email: Optional[str] = None
    
    # Entity information
    entity_type: EntityTypeInfo
    linked_entity_id: UUID
    entity_name: str
    entity_details: Dict[str, Any] = Field(
        default_factory=dict,
        description="Full entity details including contact info, specialty, etc."
    )
    
    # Status and scoring
    relationship_status: RelationshipStatusInfo
    loyalty_status: Optional[LoyaltyStatusInfo] = None
    lead_score: Optional[int] = Field(None, ge=1, le=5)
    
    # Activity information
    last_activity_date: Optional[datetime] = None
    next_steps: Optional[str] = None
    engagement_frequency: Optional[str] = None
    
    # Related data
    campaigns: List[CampaignInfo] = Field(default_factory=list)
    metrics: Optional[RelationshipMetrics] = None
    recent_activities: List[ActivityLogItem] = Field(
        default_factory=list,
        description="Last 10 activities"
    )
    
    # Timestamps
    created_at: datetime
    updated_at: datetime


# Filter schemas
class RelationshipFilters(BaseModel):
    """Filters for relationship list endpoint."""
    # User filters
    user_ids: Optional[List[int]] = None
    my_relationships_only: bool = False
    
    # Entity filters
    entity_type_ids: Optional[List[int]] = None
    entity_ids: Optional[List[UUID]] = None
    
    # Status filters
    relationship_status_ids: Optional[List[int]] = None
    loyalty_status_ids: Optional[List[int]] = None
    lead_scores: Optional[List[int]] = Field(None, description="List of scores 1-5")
    
    # Activity filters
    last_activity_after: Optional[date] = None
    last_activity_before: Optional[date] = None
    days_since_activity_min: Optional[int] = None
    days_since_activity_max: Optional[int] = None
    
    # Campaign filters
    campaign_ids: Optional[List[UUID]] = None
    
    # Search
    search_text: Optional[str] = Field(None, description="Search in entity names and notes")
    
    # Geographic filters (for contacts/sites)
    geographies: Optional[List[str]] = None
    cities: Optional[List[str]] = None
    
    # Specialty filters (for contacts/providers)
    specialties: Optional[List[str]] = None


class FilterOptionsResponse(BaseModel):
    """Available filter options for dropdowns."""
    users: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="User options with id, name, and relationship count"
    )
    entity_types: List[EntityTypeInfo]
    relationship_statuses: List[RelationshipStatusInfo]
    loyalty_statuses: List[LoyaltyStatusInfo]
    campaigns: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Active campaigns with id and name"
    )
    geographies: List[str] = Field(default_factory=list)
    specialties: List[str] = Field(default_factory=list)


# Update schemas
class RelationshipUpdate(BaseModel):
    """Schema for updating a relationship."""
    relationship_status_id: Optional[int] = None
    loyalty_status_id: Optional[int] = None
    lead_score: Optional[int] = Field(None, ge=1, le=5)
    next_steps: Optional[str] = None
    engagement_frequency: Optional[str] = None


class BulkRelationshipUpdate(BaseModel):
    """Schema for bulk updating relationships."""
    relationship_ids: List[UUID]
    updates: RelationshipUpdate


class RelationshipUpdateResponse(BaseModel):
    """Response after updating relationship(s)."""
    updated_count: int
    relationships: List[RelationshipListItem]
    message: str


# Activity logging schemas
class ActivityLogCreate(BaseModel):
    """Schema for logging a new activity against a relationship."""
    activity_date: date
    subject: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    activity_type: str = Field(..., description="Call, Email, Meeting, etc.")
    status: str = Field(default="Completed")
    

class ActivityLogResponse(BaseModel):
    """Response after logging an activity."""
    activity_id: UUID
    relationship_id: UUID
    message: str
    updated_relationship: RelationshipListItem


# Export schemas
class ExportRequest(BaseModel):
    """Request for exporting relationship data."""
    filters: Optional[RelationshipFilters] = None
    format: str = Field(default="csv", pattern="^(csv|excel)$")
    include_activities: bool = False
    include_metrics: bool = True