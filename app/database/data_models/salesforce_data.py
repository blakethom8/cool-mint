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
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
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

    # Primary key and relationships
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    salesforce_id = Column(String(18), unique=True, nullable=False, index=True)
    contact_id = Column(UUID(as_uuid=True), ForeignKey("sf_contacts.id"))

    # Standard Fields
    subject = Column(String(255))
    activity_date = Column(Date)
    status = Column(String(255), nullable=False)  # Required in SF
    priority = Column(String(20), nullable=False)  # Required in SF
    is_high_priority = Column(Boolean, nullable=False)
    description = Column(Text)  # Length: 32000
    is_deleted = Column(Boolean, nullable=False)
    is_closed = Column(Boolean, nullable=False)
    is_archived = Column(Boolean, nullable=False)
    task_subtype = Column(String(40))
    completed_datetime = Column(DateTime)
    who_count = Column(Integer)
    what_count = Column(Integer)

    # Custom Fields
    mno_subtype = Column(String(255))  # MNO_Subtype_c__c
    mno_primary_attendees_id = Column(String(18))  # References Primary_Contact__c
    mno_type = Column(String(255))
    mn_tags = Column(Text)  # multipicklist, Length: 4099
    mno_setting = Column(String(255))
    attendees_concatenation = Column(Text)
    comments_short = Column(Text)

    # Relationship Fields
    who_id = Column(String(18))  # References Contact, Lead
    what_id = Column(String(18))  # References multiple objects
    owner_id = Column(String(18), nullable=False)  # References Group, User
    account_id = Column(String(18))  # References Account
    created_by_id = Column(String(18), nullable=False)  # References User
    last_modified_by_id = Column(String(18), nullable=False)  # References User

    # System Fields
    sf_created_date = Column(DateTime, nullable=False)
    sf_last_modified_date = Column(DateTime, nullable=False)
    sf_system_modstamp = Column(DateTime, nullable=False)

    # Event-specific fields (for when type = 'Event')
    start_datetime = Column(DateTime)
    end_datetime = Column(DateTime)
    duration_minutes = Column(Integer)
    location = Column(String(255))
    show_as = Column(String(40))
    is_all_day_event = Column(Boolean)
    is_private = Column(Boolean)

    # Local metadata
    type = Column(String(50))  # 'Task' or 'Event'
    last_synced_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    created_at = Column(DateTime, default=datetime.now)

    # Additional data as JSON for flexibility
    additional_data = Column(JSON)

    # LLM Analysis results
    analysis_results = Column(JSON)
    last_analyzed_at = Column(DateTime)

    # Relationships
    contact = relationship("SfContact", back_populates="activities")

    # Indexes for common queries
    __table_args__ = (
        Index("idx_sf_activity_salesforce_id", "salesforce_id"),
        Index("idx_sf_activity_contact_id", "contact_id"),
        Index("idx_sf_activity_who_id", "who_id"),
        Index("idx_sf_activity_what_id", "what_id"),
        Index("idx_sf_activity_owner_id", "owner_id"),
        Index("idx_sf_activity_account_id", "account_id"),
        Index("idx_sf_activity_activity_date", "activity_date"),
        Index("idx_sf_activity_status", "status"),
        Index("idx_sf_activity_is_closed", "is_closed"),
        Index("idx_sf_activity_last_modified", "sf_last_modified_date"),
        Index("idx_sf_activity_type", "type"),
    )


class SfUser(Base):
    """Model for Salesforce User data."""

    __tablename__ = "sf_users"

    id = Column(Integer, primary_key=True)
    salesforce_id = Column(String(18), unique=True, nullable=False)

    # Standard Fields
    username = Column(String(80), nullable=False)
    last_name = Column(String(80), nullable=False)
    first_name = Column(String(40))
    middle_name = Column(String(40))
    suffix = Column(String(40))
    name = Column(String(121), nullable=False)
    email = Column(String(128), nullable=False)
    is_profile_photo_active = Column(Boolean, nullable=False)
    address = Column(JSONB)  # Store address as JSON

    # Custom Fields
    external_id = Column(String(20))

    # System Fields
    sf_created_date = Column(DateTime, nullable=False)
    sf_last_modified_date = Column(DateTime, nullable=False)
    sf_system_modstamp = Column(DateTime, nullable=False)

    # Local metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SfTaskWhoRelation(Base):
    """Model for Salesforce TaskWhoRelation data."""

    __tablename__ = "sf_taskwhorelations"

    id = Column(Integer, primary_key=True)
    salesforce_id = Column(String(18), unique=True, nullable=False)

    # Standard Fields
    is_deleted = Column(Boolean, nullable=False)
    type = Column(String(50))

    # Relationship Fields
    relation_id = Column(String(18), ForeignKey("sf_contacts.salesforce_id"))
    task_id = Column(String(18), ForeignKey("sf_activities.salesforce_id"))
    created_by_id = Column(
        String(18), ForeignKey("sf_users.salesforce_id"), nullable=False
    )
    last_modified_by_id = Column(
        String(18), ForeignKey("sf_users.salesforce_id"), nullable=False
    )

    # System Fields
    sf_created_date = Column(DateTime, nullable=False)
    sf_last_modified_date = Column(DateTime, nullable=False)
    sf_system_modstamp = Column(DateTime, nullable=False)

    # Local metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    contact = relationship("SfContact", foreign_keys=[relation_id])
    task = relationship("SfActivity", foreign_keys=[task_id])
    created_by = relationship("SfUser", foreign_keys=[created_by_id])
    last_modified_by = relationship("SfUser", foreign_keys=[last_modified_by_id])
