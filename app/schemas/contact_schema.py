from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ContactMapMarker(BaseModel):
    """Minimal contact data for map markers"""
    id: str
    salesforce_id: str
    name: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    mailing_address: Optional[str] = None
    contact_count: int = 1  # Number of contacts at this address
    specialty: Optional[str] = None
    organization: Optional[str] = None


class ContactListItem(BaseModel):
    """Contact data for list views"""
    id: str
    salesforce_id: str
    name: str
    first_name: Optional[str] = None
    last_name: str
    title: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    specialty: Optional[str] = None
    organization: Optional[str] = None
    mailing_address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    is_physician: bool = False
    active: bool = True
    last_activity_date: Optional[datetime] = None


class ContactDetail(BaseModel):
    """Full contact information"""
    id: str
    salesforce_id: str
    
    # Name fields
    first_name: Optional[str] = None
    last_name: str
    middle_name: Optional[str] = None
    salutation: Optional[str] = None
    suffix: Optional[str] = None
    name: str
    full_name: Optional[str] = None
    
    # Contact information
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile_phone: Optional[str] = None
    fax: Optional[str] = None
    home_phone: Optional[str] = None
    other_phone: Optional[str] = None
    title: Optional[str] = None
    
    # Address information
    mailing_street: Optional[str] = None
    mailing_city: Optional[str] = None
    mailing_state: Optional[str] = None
    mailing_postal_code: Optional[str] = None
    mailing_country: Optional[str] = None
    mailing_latitude: Optional[float] = None
    mailing_longitude: Optional[float] = None
    mailing_address_compound: Optional[str] = None
    
    # Professional information
    specialty: Optional[str] = None
    npi: Optional[str] = None
    is_physician: bool = False
    active: bool = True
    organization: Optional[str] = Field(None, alias="contact_account_name")
    
    # Activity information
    last_activity_date: Optional[datetime] = None
    days_since_last_visit: Optional[float] = None
    
    # Custom fields
    external_id: Optional[str] = None
    epic_id: Optional[str] = None
    geography: Optional[str] = None
    primary_geography: Optional[str] = None
    primary_mgma_specialty: Optional[str] = None
    network_picklist: Optional[str] = None
    panel_status: Optional[str] = None
    
    class Config:
        populate_by_name = True


class ContactFilterOptions(BaseModel):
    """Available filter options for contacts"""
    specialties: List[str] = Field(default_factory=list)
    organizations: List[str] = Field(default_factory=list)
    cities: List[str] = Field(default_factory=list)
    states: List[str] = Field(default_factory=list)
    geographies: List[str] = Field(default_factory=list)
    panel_statuses: List[str] = Field(default_factory=list)


class ContactFilters(BaseModel):
    """Filter parameters for contact queries"""
    search: Optional[str] = None
    specialty: Optional[str] = None
    organization: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    geography: Optional[str] = None
    is_physician: Optional[bool] = None
    active: Optional[bool] = True
    panel_status: Optional[str] = None
    # Geographic bounds for map viewport
    north: Optional[float] = None
    south: Optional[float] = None
    east: Optional[float] = None
    west: Optional[float] = None


class ContactListResponse(BaseModel):
    """Paginated response for contact lists"""
    items: List[ContactListItem]
    total: int
    page: int
    page_size: int
    has_more: bool


class ContactMapResponse(BaseModel):
    """Response for map marker data"""
    markers: List[ContactMapMarker]
    total: int
    clustered: bool = False
    bounds: Optional[Dict[str, float]] = None  # north, south, east, west