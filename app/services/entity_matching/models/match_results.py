"""Data models for entity matching results"""
from dataclasses import dataclass
from typing import Dict, Any, Optional
from enum import Enum


class EntityType(str, Enum):
    """Types of entities that can be matched"""
    CONTACT = "contact"
    PROVIDER_GROUP = "provider_group"
    SITE_OF_SERVICE = "site_of_service"


class MatchType(str, Enum):
    """Types of matches"""
    # Exact matches
    EMAIL = "email"
    NPI = "npi"
    EXTERNAL_ID = "external_id"
    EXACT_NAME = "exact_name"
    
    # Name-based matches
    FIRST_LAST_NAME = "first_last_name"
    LAST_NAME = "last_name"
    FUZZY_NAME = "fuzzy_name"
    
    # Other identifiers
    PHONE = "phone"
    ADDRESS = "address"
    ALIAS = "alias"


@dataclass
class MatchResult:
    """Base class for all entity match results"""
    # Entity identification
    entity_id: str
    entity_type: EntityType
    display_name: str
    
    # Match information
    match_type: MatchType
    confidence_score: float  # 0.0 to 1.0
    match_details: Dict[str, Any]
    
    # Optional fields
    active: bool = True
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            "entity_id": self.entity_id,
            "entity_type": self.entity_type.value,
            "display_name": self.display_name,
            "match_type": self.match_type.value,
            "confidence_score": round(self.confidence_score, 3),
            "match_details": self.match_details,
            "active": self.active
        }


@dataclass
class ContactMatch(MatchResult):
    """Match result specific to contacts"""
    # Contact-specific fields
    salesforce_id: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    specialty: Optional[str] = None
    organization: Optional[str] = None
    npi: Optional[str] = None
    
    def __post_init__(self):
        """Ensure entity type is set correctly"""
        self.entity_type = EntityType.CONTACT
    
    def to_dict(self) -> Dict:
        """Extended dictionary conversion for contacts"""
        base_dict = super().to_dict()
        base_dict.update({
            "salesforce_id": self.salesforce_id,
            "email": self.email,
            "phone": self.phone,
            "specialty": self.specialty,
            "organization": self.organization,
            "npi": self.npi
        })
        return base_dict


@dataclass
class ProviderGroupMatch(MatchResult):
    """Match result specific to provider groups"""
    # Provider group-specific fields
    group_npi: Optional[str] = None
    member_count: Optional[int] = None
    specialties: Optional[list[str]] = None
    primary_location: Optional[str] = None
    
    def __post_init__(self):
        """Ensure entity type is set correctly"""
        self.entity_type = EntityType.PROVIDER_GROUP
    
    def to_dict(self) -> Dict:
        """Extended dictionary conversion for provider groups"""
        base_dict = super().to_dict()
        base_dict.update({
            "group_npi": self.group_npi,
            "member_count": self.member_count,
            "specialties": self.specialties,
            "primary_location": self.primary_location
        })
        return base_dict


@dataclass
class SiteOfServiceMatch(MatchResult):
    """Match result specific to sites of service"""
    # Site-specific fields
    site_type: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    phone: Optional[str] = None
    
    def __post_init__(self):
        """Ensure entity type is set correctly"""
        self.entity_type = EntityType.SITE_OF_SERVICE
    
    def to_dict(self) -> Dict:
        """Extended dictionary conversion for sites"""
        base_dict = super().to_dict()
        base_dict.update({
            "site_type": self.site_type,
            "address": self.address,
            "city": self.city,
            "state": self.state,
            "zip_code": self.zip_code,
            "phone": self.phone
        })
        return base_dict


@dataclass
class MatchContext:
    """Context information to help with matching"""
    organization: Optional[str] = None
    specialty: Optional[str] = None
    location: Optional[str] = None
    entity_type_hint: Optional[EntityType] = None
    user_context: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict:
        """Convert context to dictionary"""
        return {
            k: v for k, v in {
                "organization": self.organization,
                "specialty": self.specialty,
                "location": self.location,
                "entity_type_hint": self.entity_type_hint.value if self.entity_type_hint else None,
                "user_context": self.user_context
            }.items() if v is not None
        }