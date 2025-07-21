import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    String,
    Integer,
    Text,
    ForeignKey,
    Numeric,
    Float,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from database.session import Base

"""
Claims Data Database Models Module

This module defines the SQLAlchemy models for the claims-based Market Explorer.
It includes models for:
1. ClaimsProvider: Healthcare providers from claims data
2. SiteOfService: Healthcare facilities/locations
3. ClaimsVisit: Individual visit records linking providers to sites
4. MarketNotes: User-generated notes for market intelligence
5. LeadClassifications: Provider/site classification for lead management

These models support the claims-based market exploration functionality.
"""


class ClaimsProvider(Base):
    """SQLAlchemy model for storing healthcare provider information from claims data.
    
    This model stores provider metadata extracted from claims data including
    NPI, specialty information, and primary practice affiliations.
    """
    
    __tablename__ = "claims_providers"
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        doc="Unique identifier for the provider"
    )
    npi = Column(
        String(10),
        unique=True,
        nullable=False,
        index=True,
        doc="National Provider Identifier (NPI) - 10 digit unique identifier"
    )
    name = Column(
        String(200),
        nullable=False,
        doc="Provider's full name"
    )
    specialty = Column(
        String(200),
        nullable=False,
        doc="Provider's primary medical specialty"
    )
    geomarket = Column(
        String(100),
        doc="Geographic market area"
    )
    provider_group = Column(
        String(300),
        doc="Provider group or organization affiliation"
    )
    specialty_grandparent = Column(
        String(200),
        doc="High-level specialty category"
    )
    service_line = Column(
        String(200),
        doc="Service line category"
    )
    top_payer = Column(
        String(200),
        doc="Primary payer"
    )
    top_payer_percent = Column(
        Float,
        doc="Percentage of business from top payer"
    )
    top_referring_org = Column(
        String(300),
        doc="Top referring organization"
    )
    top_sos_name = Column(
        String(300),
        doc="Primary site of service name"
    )
    top_sos_latitude = Column(
        Float,
        doc="Latitude of primary site of service"
    )
    top_sos_longitude = Column(
        Float,
        doc="Longitude of primary site of service"
    )
    top_sos_address = Column(
        String(500),
        doc="Address of primary site of service"
    )
    top_sos_id = Column(
        String(500),
        doc="Identifier for primary site of service"
    )
    total_visits = Column(
        Integer,
        default=0,
        doc="Total number of visits across all sites"
    )
    
    created_at = Column(
        DateTime,
        default=datetime.now,
        doc="Timestamp when the provider record was created"
    )
    updated_at = Column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
        doc="Timestamp when the provider record was last updated"
    )
    
    # Relationships
    visits = relationship("ClaimsVisit", back_populates="provider")
    notes = relationship("MarketNotes", 
                        foreign_keys="MarketNotes.provider_id",
                        back_populates="provider")
    classifications = relationship("LeadClassifications",
                                 foreign_keys="LeadClassifications.provider_id",
                                 back_populates="provider")
    
    # Indexes for common queries
    __table_args__ = (
        Index("idx_claims_providers_npi", "npi"),
        Index("idx_claims_providers_specialty", "specialty"),
        Index("idx_claims_providers_geomarket", "geomarket"),
        Index("idx_claims_providers_provider_group", "provider_group"),
        Index("idx_claims_providers_name", "name"),
    )


class SiteOfService(Base):
    """SQLAlchemy model for storing site of service (healthcare facility) information.
    
    This model stores facility metadata including location, type, and geographic data.
    """
    
    __tablename__ = "claims_sites_of_service"
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        doc="Unique identifier for the site"
    )
    legacy_id = Column(
        String(500),
        unique=True,
        nullable=False,
        index=True,
        doc="Legacy identifier (name + address) for backward compatibility"
    )
    name = Column(
        String(300),
        nullable=False,
        doc="Site of service name"
    )
    city = Column(
        String(100),
        doc="City where the site is located"
    )
    county = Column(
        String(100),
        doc="County where the site is located"
    )
    site_type = Column(
        String(100),
        doc="Type of facility (Hospital, Clinic, Practice, etc.)"
    )
    zip_code = Column(
        String(10),
        doc="ZIP code of the site"
    )
    latitude = Column(
        Float,
        doc="Latitude coordinate"
    )
    longitude = Column(
        Float,
        doc="Longitude coordinate"
    )
    geomarket = Column(
        String(100),
        doc="Geographic market area"
    )
    address = Column(
        String(500),
        doc="Full address of the site"
    )
    
    created_at = Column(
        DateTime,
        default=datetime.now,
        doc="Timestamp when the site record was created"
    )
    updated_at = Column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
        doc="Timestamp when the site record was last updated"
    )
    
    # Relationships
    visits = relationship("ClaimsVisit", back_populates="site")
    notes = relationship("MarketNotes",
                        foreign_keys="MarketNotes.site_id",
                        back_populates="site")
    classifications = relationship("LeadClassifications",
                                 foreign_keys="LeadClassifications.site_id",
                                 back_populates="site")
    
    # Indexes for common queries
    __table_args__ = (
        Index("idx_sites_of_service_legacy_id", "legacy_id"),
        Index("idx_sites_of_service_name", "name"),
        Index("idx_sites_of_service_location", "city", "county"),
        Index("idx_sites_of_service_type", "site_type"),
        Index("idx_sites_of_service_geomarket", "geomarket"),
        Index("idx_sites_of_service_coordinates", "latitude", "longitude"),
    )


class ClaimsVisit(Base):
    """SQLAlchemy model for storing visit data linking providers to sites of service.
    
    This is the fact table that connects providers to sites with visit volume
    and service type information.
    """
    
    __tablename__ = "claims_visits"
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        doc="Unique identifier for the visit record"
    )
    provider_id = Column(
        UUID(as_uuid=True),
        ForeignKey("claims_providers.id"),
        nullable=False,
        doc="Foreign key reference to the provider"
    )
    site_id = Column(
        UUID(as_uuid=True),
        ForeignKey("claims_sites_of_service.id"),
        nullable=False,
        doc="Foreign key reference to the site of service"
    )
    visits = Column(
        Integer,
        nullable=False,
        default=0,
        doc="Number of visits for this provider-site combination"
    )
    has_oncology = Column(
        Boolean,
        default=False,
        doc="Whether visits include oncology services"
    )
    has_surgery = Column(
        Boolean,
        default=False,
        doc="Whether visits include surgical services"
    )
    has_inpatient = Column(
        Boolean,
        default=False,
        doc="Whether visits include inpatient services"
    )
    
    created_at = Column(
        DateTime,
        default=datetime.now,
        doc="Timestamp when the visit record was created"
    )
    updated_at = Column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
        doc="Timestamp when the visit record was last updated"
    )
    
    # Relationships
    provider = relationship("ClaimsProvider", back_populates="visits")
    site = relationship("SiteOfService", back_populates="visits")
    
    # Indexes for common queries
    __table_args__ = (
        Index("idx_claims_visits_provider_site", "provider_id", "site_id"),
        Index("idx_claims_visits_provider", "provider_id"),
        Index("idx_claims_visits_site", "site_id"),
        Index("idx_claims_visits_volume", "visits"),
        Index("idx_claims_visits_services", "has_oncology", "has_surgery", "has_inpatient"),
    )


class MarketNotes(Base):
    """SQLAlchemy model for storing user-generated notes for market intelligence.
    
    This model stores notes that can be attached to providers, sites, or provider groups
    for tracking market insights, relationships, and opportunities.
    """
    
    __tablename__ = "market_notes"
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        doc="Unique identifier for the note"
    )
    provider_id = Column(
        UUID(as_uuid=True),
        ForeignKey("claims_providers.id"),
        nullable=True,
        doc="Foreign key reference to provider (if note is about a provider)"
    )
    site_id = Column(
        UUID(as_uuid=True),
        ForeignKey("claims_sites_of_service.id"),
        nullable=True,
        doc="Foreign key reference to site (if note is about a site)"
    )
    provider_group = Column(
        String(300),
        nullable=True,
        doc="Provider group name (if note is about a provider group)"
    )
    note_type = Column(
        String(50),
        nullable=False,
        default="general",
        doc="Type of note: general, relationship, opportunity, challenge"
    )
    title = Column(
        String(200),
        doc="Short title or summary of the note"
    )
    content = Column(
        Text,
        nullable=False,
        doc="Full content of the note"
    )
    author = Column(
        String(100),
        doc="Name or identifier of the note author"
    )
    tags = Column(
        JSON,
        doc="JSON array of tags for categorization"
    )
    
    created_at = Column(
        DateTime,
        default=datetime.now,
        doc="Timestamp when the note was created"
    )
    updated_at = Column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
        doc="Timestamp when the note was last updated"
    )
    
    # Relationships
    provider = relationship("ClaimsProvider",
                          foreign_keys=[provider_id],
                          back_populates="notes")
    site = relationship("SiteOfService",
                       foreign_keys=[site_id],
                       back_populates="notes")
    
    # Indexes for common queries
    __table_args__ = (
        Index("idx_market_notes_provider", "provider_id"),
        Index("idx_market_notes_site", "site_id"),
        Index("idx_market_notes_provider_group", "provider_group"),
        Index("idx_market_notes_type", "note_type"),
        Index("idx_market_notes_author", "author"),
        Index("idx_market_notes_created", "created_at"),
    )


class LeadClassifications(Base):
    """SQLAlchemy model for storing lead classifications for providers and sites.
    
    This model tracks how users classify different entities as leads
    (hot, warm, cold, existing relationship) for sales and outreach purposes.
    """
    
    __tablename__ = "lead_classifications"
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        doc="Unique identifier for the classification"
    )
    provider_id = Column(
        UUID(as_uuid=True),
        ForeignKey("claims_providers.id"),
        nullable=True,
        doc="Foreign key reference to provider (if classifying a provider)"
    )
    site_id = Column(
        UUID(as_uuid=True),
        ForeignKey("claims_sites_of_service.id"),
        nullable=True,
        doc="Foreign key reference to site (if classifying a site)"
    )
    provider_group = Column(
        String(300),
        nullable=True,
        doc="Provider group name (if classifying a provider group)"
    )
    classification = Column(
        String(50),
        nullable=False,
        doc="Classification type: hot_lead, warm_lead, cold_lead, existing_relationship"
    )
    confidence_score = Column(
        Integer,
        doc="Confidence score from 1-10 for the classification"
    )
    reason = Column(
        Text,
        doc="Reasoning or notes for this classification"
    )
    classified_by = Column(
        String(100),
        doc="Name or identifier of the person who made the classification"
    )
    
    created_at = Column(
        DateTime,
        default=datetime.now,
        doc="Timestamp when the classification was created"
    )
    updated_at = Column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
        doc="Timestamp when the classification was last updated"
    )
    
    # Relationships
    provider = relationship("ClaimsProvider",
                          foreign_keys=[provider_id],
                          back_populates="classifications")
    site = relationship("SiteOfService",
                       foreign_keys=[site_id],
                       back_populates="classifications")
    
    # Indexes for common queries
    __table_args__ = (
        Index("idx_lead_classifications_provider", "provider_id"),
        Index("idx_lead_classifications_site", "site_id"),
        Index("idx_lead_classifications_provider_group", "provider_group"),
        Index("idx_lead_classifications_type", "classification"),
        Index("idx_lead_classifications_classified_by", "classified_by"),
        Index("idx_lead_classifications_created", "created_at"),
    )