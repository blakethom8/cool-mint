import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    String,
    Integer,
    Text,
    ForeignKey,
    Numeric,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database.session import Base

"""
Provider CRM Database Models Module

This module defines the SQLAlchemy models for the Provider CRM application.
It includes models for:
1. Provider: Healthcare providers with their metadata
2. ProviderVisits: Aggregated visit data from claims
3. OutreachEfforts: Tracking engagement with providers
4. ProviderReferrals: Tracking referrals between providers

These models support outreach specialists in engaging with physicians 
and practices to drive referral patterns.
"""


class Provider(Base):
    """SQLAlchemy model for storing healthcare provider information.

    This model stores core provider metadata including NPI, specialty,
    and primary practice location information.
    """

    __tablename__ = "providers"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        doc="Unique identifier for the provider",
    )
    npi = Column(
        String(10),
        unique=True,
        nullable=False,
        index=True,
        doc="National Provider Identifier (NPI) - 10 digit unique identifier",
    )
    first_name = Column(String(100), nullable=False, doc="Provider's first name")
    last_name = Column(String(100), nullable=False, doc="Provider's last name")
    primary_specialty = Column(
        String(200), nullable=False, doc="Provider's primary medical specialty"
    )
    primary_practice_name = Column(
        String(300), doc="Name of the primary practice/organization"
    )
    primary_organization = Column(
        String(300),
        doc="Parent healthcare organization or system that employs the provider",
    )
    primary_practice_address = Column(
        String(500), doc="Full address of the primary practice location"
    )
    primary_practice_city = Column(String(100), doc="City of the primary practice")
    primary_practice_state = Column(
        String(2), doc="State abbreviation of the primary practice"
    )
    primary_practice_zip = Column(String(10), doc="ZIP code of the primary practice")
    phone = Column(String(20), doc="Primary contact phone number")
    email = Column(String(255), doc="Primary contact email address")

    created_at = Column(
        DateTime,
        default=datetime.now,
        doc="Timestamp when the provider record was created",
    )
    updated_at = Column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
        doc="Timestamp when the provider record was last updated",
    )

    # Relationships
    visits = relationship("ProviderVisits", back_populates="provider")
    outreach_efforts = relationship("OutreachEfforts", back_populates="provider")
    referrals_sent = relationship(
        "ProviderReferrals",
        foreign_keys="ProviderReferrals.referring_provider_id",
        back_populates="referring_provider",
    )
    referrals_received = relationship(
        "ProviderReferrals",
        foreign_keys="ProviderReferrals.referred_to_provider_id",
        back_populates="referred_to_provider",
    )


class ProviderVisits(Base):
    """SQLAlchemy model for storing aggregated provider visit data from claims.

    This model stores aggregated visit information per provider, specialty,
    location, and services rendered. Data is typically sourced from claims data.
    """

    __tablename__ = "provider_visits"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        doc="Unique identifier for the visit record",
    )
    provider_id = Column(
        UUID(as_uuid=True),
        ForeignKey("providers.id"),
        nullable=False,
        doc="Foreign key reference to the provider",
    )
    specialty = Column(
        String(200), nullable=False, doc="Medical specialty for these visits"
    )
    practice_location = Column(
        String(500), doc="Practice location where visits occurred"
    )
    services_rendered = Column(
        String(500), doc="Description of services rendered during visits"
    )
    visit_count = Column(
        Integer,
        nullable=False,
        default=0,
        doc="Total number of visits for this aggregation",
    )
    total_charges = Column(
        Numeric(12, 2), doc="Total charges for all visits in this aggregation"
    )
    visit_start_date = Column(
        DateTime,
        nullable=False,
        doc="Start date of the visit period for this aggregation",
    )
    visit_end_date = Column(
        DateTime,
        nullable=False,
        doc="End date of the visit period for this aggregation",
    )

    created_at = Column(
        DateTime,
        default=datetime.now,
        doc="Timestamp when the visit record was created",
    )
    updated_at = Column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
        doc="Timestamp when the visit record was last updated",
    )

    # Relationships
    provider = relationship("Provider", back_populates="visits")

    # Indexes for common queries
    __table_args__ = (
        Index(
            "idx_provider_visits_provider_period",
            "provider_id",
            "visit_start_date",
            "visit_end_date",
        ),
        Index("idx_provider_visits_specialty", "specialty"),
    )


class OutreachEfforts(Base):
    """SQLAlchemy model for tracking outreach specialist engagement with providers.

    This model tracks all outreach activities including dates, effort types,
    and detailed comments about the engagement.
    """

    __tablename__ = "outreach_efforts"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        doc="Unique identifier for the outreach effort",
    )
    provider_id = Column(
        UUID(as_uuid=True),
        ForeignKey("providers.id"),
        nullable=False,
        doc="Foreign key reference to the provider being contacted",
    )
    outreach_date = Column(
        DateTime, nullable=False, doc="Date and time when the outreach effort occurred"
    )
    outreach_type = Column(
        String(100),
        nullable=False,
        doc="Type of outreach effort (e.g., 'phone_call', 'email', 'in_person_visit', 'conference')",
    )
    outreach_specialist = Column(
        String(200), doc="Name or identifier of the outreach specialist"
    )
    comments = Column(
        Text,
        doc="Detailed comments about the outreach effort, conversation notes, and follow-up actions",
    )
    follow_up_required = Column(
        String(10), default="No", doc="Whether follow-up is required (Yes/No)"
    )
    follow_up_date = Column(DateTime, doc="Scheduled date for follow-up if required")

    created_at = Column(
        DateTime,
        default=datetime.now,
        doc="Timestamp when the outreach effort record was created",
    )
    updated_at = Column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
        doc="Timestamp when the outreach effort record was last updated",
    )

    # Relationships
    provider = relationship("Provider", back_populates="outreach_efforts")

    # Indexes for common queries
    __table_args__ = (
        Index("idx_outreach_efforts_provider_date", "provider_id", "outreach_date"),
        Index("idx_outreach_efforts_type", "outreach_type"),
        Index("idx_outreach_efforts_specialist", "outreach_specialist"),
        Index("idx_outreach_efforts_follow_up", "follow_up_required", "follow_up_date"),
    )


class ProviderReferrals(Base):
    """SQLAlchemy model for tracking referrals between providers.

    This model stores aggregated referral data between providers including
    the referring provider, referred-to provider, reason for referral,
    and aggregated counts for a given time period.
    """

    __tablename__ = "provider_referrals"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        doc="Unique identifier for the referral record",
    )
    referring_provider_id = Column(
        UUID(as_uuid=True),
        ForeignKey("providers.id"),
        nullable=False,
        doc="Foreign key reference to the provider making the referral",
    )
    referred_to_provider_id = Column(
        UUID(as_uuid=True),
        ForeignKey("providers.id"),
        nullable=False,
        doc="Foreign key reference to the provider receiving the referral",
    )
    referral_reason = Column(
        String(500),
        nullable=False,
        doc="Reason for the referral (e.g., specialty consultation, procedure, etc.)",
    )
    referral_count = Column(
        Integer,
        nullable=False,
        default=0,
        doc="Total number of referrals for this aggregation",
    )
    referral_start_date = Column(
        DateTime,
        nullable=False,
        doc="Start date of the referral period for this aggregation",
    )
    referral_end_date = Column(
        DateTime,
        nullable=False,
        doc="End date of the referral period for this aggregation",
    )

    created_at = Column(
        DateTime,
        default=datetime.now,
        doc="Timestamp when the referral record was created",
    )
    updated_at = Column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
        doc="Timestamp when the referral record was last updated",
    )

    # Relationships
    referring_provider = relationship(
        "Provider",
        foreign_keys=[referring_provider_id],
        back_populates="referrals_sent",
    )
    referred_to_provider = relationship(
        "Provider",
        foreign_keys=[referred_to_provider_id],
        back_populates="referrals_received",
    )

    # Indexes for common queries
    __table_args__ = (
        Index(
            "idx_provider_referrals_referring_period",
            "referring_provider_id",
            "referral_start_date",
            "referral_end_date",
        ),
        Index(
            "idx_provider_referrals_referred_to_period",
            "referred_to_provider_id",
            "referral_start_date",
            "referral_end_date",
        ),
        Index("idx_provider_referrals_reason", "referral_reason"),
        Index(
            "idx_provider_referrals_provider_pair",
            "referring_provider_id",
            "referred_to_provider_id",
        ),
    )
