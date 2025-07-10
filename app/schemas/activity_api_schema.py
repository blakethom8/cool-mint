from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ActivityContactInfo(BaseModel):
    contact_id: str
    contact_name: str
    contact_type: Optional[str] = None
    specialty: Optional[str] = None
    organization: Optional[str] = None
    city: Optional[str] = None


class ActivityListItem(BaseModel):
    id: str
    activity_id: str
    activity_date: datetime
    subject: str
    description: Optional[str] = None
    mno_type: Optional[str] = None
    mno_subtype: Optional[str] = None
    owner_name: Optional[str] = None
    owner_id: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    type: Optional[str] = None
    contact_count: int = 0
    contact_names: List[str] = Field(default_factory=list)
    contact_specialties: List[str] = Field(default_factory=list)
    has_contact: bool = False
    has_md_contact: bool = False
    has_pharma_contact: bool = False
    has_other_contact: bool = False


class ActivityDetail(BaseModel):
    id: str
    activity_id: str
    activity_date: datetime
    subject: str
    description: Optional[str] = None
    mno_type: Optional[str] = None
    mno_subtype: Optional[str] = None
    owner_name: Optional[str] = None
    owner_id: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    type: Optional[str] = None
    due_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None
    contacts: List[ActivityContactInfo] = Field(default_factory=list)
    llm_context_json: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class ActivityFilters(BaseModel):
    owner_ids: Optional[List[str]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    search_text: Optional[str] = None
    has_contact: Optional[bool] = None
    has_md_contact: Optional[bool] = None
    has_pharma_contact: Optional[bool] = None
    contact_ids: Optional[List[str]] = None
    contact_specialties: Optional[List[str]] = None
    mno_types: Optional[List[str]] = None
    mno_subtypes: Optional[List[str]] = None
    statuses: Optional[List[str]] = None
    types: Optional[List[str]] = None


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=100)
    sort_by: str = Field(default="activity_date")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")


class ActivityListResponse(BaseModel):
    activities: List[ActivityListItem]
    total_count: int
    page: int
    page_size: int
    total_pages: int


class ActivitySelectionRequest(BaseModel):
    activity_ids: List[str] = Field(description="List of activity IDs to process")
    prompt: Optional[str] = Field(None, description="Custom prompt for LLM processing")
    bundle_name: Optional[str] = Field(None, description="Name for the activity bundle")
    bundle_description: Optional[str] = Field(None, description="Description of the bundle")


class FilterOptionsResponse(BaseModel):
    owners: List[Dict[str, str]]  # [{id, name}]
    contact_specialties: List[str]
    mno_types: List[str]
    mno_subtypes: List[str]
    statuses: List[str]
    types: List[str]
