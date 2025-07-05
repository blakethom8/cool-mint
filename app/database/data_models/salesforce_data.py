from datetime import datetime
import uuid
from sqlalchemy import (
    Column,
    DateTime,
    String,
    Text,
    ForeignKey,
    JSON,
    Index,
    Boolean,
    Date,
    Float,
    Integer,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database.session import Base


class SfContact(Base):
    """SQLAlchemy model for storing Salesforce Contact information."""

    __tablename__ = "sf_contacts"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    salesforce_id = Column(String(18), unique=True, nullable=False, index=True)

    # Standard Fields - Core Identity
    last_name = Column(String(80), nullable=False)  # Required in SF
    first_name = Column(String(40))
    salutation = Column(String(40))
    middle_name = Column(String(40))
    suffix = Column(String(40))
    name = Column(String(121))  # Full name, auto-generated in SF

    # Standard Fields - Contact Information
    email = Column(String(80))
    phone = Column(String(40))
    fax = Column(String(40))
    mobile_phone = Column(String(40))
    home_phone = Column(String(40))
    other_phone = Column(String(40))
    title = Column(String(128))

    # Standard Fields - Mailing Address
    mailing_street = Column(Text)  # textarea in SF
    mailing_city = Column(String(40))
    mailing_state = Column(String(80))
    mailing_postal_code = Column(String(20))
    mailing_country = Column(String(80))
    mailing_latitude = Column(Float)
    mailing_longitude = Column(Float)
    mailing_geocode_accuracy = Column(String(40))

    # Standard Fields - Activity Tracking
    last_activity_date = Column(Date)
    last_viewed_date = Column(DateTime)
    last_referenced_date = Column(DateTime)

    # Custom Fields - Identity & Classification
    external_id = Column(String(20))
    full_name = Column(String(1300))
    npi = Column(String(20))
    specialty = Column(String(255))
    is_physician = Column(Boolean, default=False)
    is_my_contact = Column(Boolean, default=False)
    active = Column(Boolean, default=True)

    # Custom Fields - Provider Information
    days_since_last_visit = Column(Float)
    contact_account_name = Column(String(1300))
    last_visited_by_rep_id = Column(String(18))  # Reference to User

    # Custom Fields - Business Entity & Location
    business_entity_id = Column(String(18))  # Reference to Account
    mailing_address_compound = Column(String(1300))
    other_address_compound = Column(String(1300))

    # Custom Fields - Minnesota Specific
    employment_status_mn = Column(String(255))
    epic_id = Column(String(20))
    geography = Column(String(255))
    mn_physician = Column(Boolean, default=False)
    npi_mn = Column(String(20))
    network_id = Column(String(18))  # Reference to Network__c
    network_picklist = Column(String(255))
    onboarding_tasks = Column(Boolean, default=False)
    outreach_focus = Column(Boolean, default=False)
    panel_status = Column(String(255))
    primary_address = Column(String(250))
    primary_geography = Column(String(255))
    primary_mgma_specialty = Column(String(255))
    primary_practice_location_id = Column(
        String(18)
    )  # Reference to Practice_Locations__c
    mn_primary_sos_id = Column(String(18))  # Reference to Account
    provider_participation = Column(Text)  # multipicklist
    provider_start_date = Column(Date)
    provider_term_date = Column(Date)
    provider_type = Column(String(255))
    secondary_practice_location_id = Column(
        String(18)
    )  # Reference to Practice_Locations__c
    specialty_group = Column(String(255))
    sub_network = Column(String(255))
    sub_specialty = Column(Text)  # multipicklist
    mn_primary_geography = Column(String(255))

    # Custom Fields - MN Address Components
    mn_address_street = Column(String(255))
    mn_address_city = Column(String(40))
    mn_address_postal_code = Column(String(20))
    mn_address_state_code = Column(String(10))
    mn_address_country_code = Column(String(10))
    mn_address_latitude = Column(Float)
    mn_address_longitude = Column(Float)
    mn_address_geocode_accuracy = Column(String(40))

    # Custom Fields - Additional MN Data
    last_outreach_activity_date = Column(Date)
    mn_secondary_sos_id = Column(String(18))  # Reference to Account
    mn_mgma_specialty = Column(String(255))
    mn_specialty_group = Column(String(255))
    mn_provider_summary = Column(String(255))
    mn_provider_detailed_notes = Column(Text)
    mn_tasks_count = Column(Float)
    mn_name_specialty_network = Column(String(1300))

    # Salesforce System Fields
    sf_created_date = Column(DateTime)
    sf_last_modified_date = Column(DateTime)
    sf_system_modstamp = Column(DateTime)
    sf_last_modified_by_id = Column(String(18))  # Reference to User

    # Local metadata
    last_synced_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    created_at = Column(DateTime, default=datetime.now)

    # Additional data as JSON for flexibility
    additional_data = Column(JSON)

    # LLM Analysis results
    analysis_results = Column(JSON)
    last_analyzed_at = Column(DateTime)

    # Relationships
    activities = relationship("SfActivity", back_populates="contact")

    # Indexes for common queries
    __table_args__ = (
        Index("idx_sf_contact_salesforce_id", "salesforce_id"),
        Index("idx_sf_contact_email", "email"),
        Index("idx_sf_contact_npi", "npi"),
        Index("idx_sf_contact_specialty", "specialty"),
        Index("idx_sf_contact_last_activity", "last_activity_date"),
        Index("idx_sf_contact_last_synced", "last_synced_at"),
        Index("idx_sf_contact_is_physician", "is_physician"),
        Index("idx_sf_contact_active", "active"),
    )


class SfActivity(Base):
    """SQLAlchemy model for storing Salesforce Activity (Task/Event) information."""

    __tablename__ = "sf_activities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    salesforce_id = Column(String(18), unique=True, nullable=False, index=True)
    contact_id = Column(UUID(as_uuid=True), ForeignKey("sf_contacts.id"))

    # Activity details
    type = Column(String(50))  # 'Task' or 'Event'
    subject = Column(String(255))
    description = Column(Text)
    status = Column(String(50))
    priority = Column(String(50))
    activity_date = Column(DateTime)

    # Additional metadata as JSON for flexibility
    additional_data = Column(JSON)

    # Salesforce metadata
    sf_last_modified_date = Column(DateTime)
    sf_created_date = Column(DateTime)

    # Local metadata
    last_synced_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    created_at = Column(DateTime, default=datetime.now)

    # LLM Analysis results
    analysis_results = Column(JSON)
    last_analyzed_at = Column(DateTime)

    # Relationships
    contact = relationship("SfContact", back_populates="activities")

    # Indexes for common queries
    __table_args__ = (
        Index("idx_sf_activity_date", "activity_date"),
        Index("idx_sf_activity_last_modified", "sf_last_modified_date"),
        Index("idx_sf_activity_last_analyzed", "last_analyzed_at"),
        Index("idx_sf_activity_contact_id", "contact_id"),
    )
