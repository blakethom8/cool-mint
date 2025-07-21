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
    UniqueConstraint,
    CheckConstraint,
    ARRAY,
    Date,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from database.session import Base

# Import SfUser for relationships
from database.data_models.salesforce_data import SfUser
# Import lookup tables
from database.data_models.crm_lookups import RelationshipStatusTypes, LoyaltyStatusTypes, EntityTypes

"""
Relationship Management Database Models

This module defines the SQLAlchemy models for the CRM relationship management system.
It includes models for:
1. Campaigns: Strategic initiatives for physician liaisons
2. Campaign_Target_Specialties: Links campaigns to specialties
3. Relationships: Tracks liaison-contact/provider relationships
4. Campaign_Relationships: Links relationships to campaigns
5. Activity_Logs: Records all interactions
6. Activity_Relationships: Links activities to relationships
7. Content_Library: Marketing materials storage
8. Campaign_Content: Links content to campaigns
9. Relationship_History: Tracks relationship progression
10. Relationship_Metrics: KPI tracking
11. Reminders: Action tracking
12. Salesforce_Sync: Integration tracking
13. LLM_Processing_Queue: Queue for AI processing
14. Next_Best_Actions: AI-generated recommendations
"""


class Campaigns(Base):
    """Defines strategic initiatives or focus areas for physician liaisons."""
    
    __tablename__ = "campaigns"
    
    campaign_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        doc="Unique identifier for the campaign"
    )
    campaign_name = Column(
        String(255),
        nullable=False,
        index=True,
        doc="Name of the campaign"
    )
    description = Column(
        Text,
        doc="Detailed description of campaign goals"
    )
    start_date = Column(
        Date,
        nullable=False,
        index=True,
        doc="Campaign start date"
    )
    end_date = Column(
        Date,
        index=True,
        doc="Campaign end date (nullable for ongoing)"
    )
    owner_user_id = Column(
        Integer,
        ForeignKey("sf_users.id"),
        nullable=False,
        index=True,
        doc="The user primarily responsible for the campaign"
    )
    status = Column(
        String(50),
        default='Active',
        index=True,
        doc="Campaign status (e.g., 'Active', 'Completed', 'Paused')"
    )
    budget = Column(
        Numeric(10, 2),
        doc="Campaign budget allocation"
    )
    target_metrics = Column(
        JSONB,
        doc="JSON object containing target KPIs and goals"
    )
    actual_metrics = Column(
        JSONB,
        doc="JSON object containing actual performance metrics"
    )
    created_at = Column(
        DateTime(timezone=True),
        default=datetime.now,
        nullable=False,
        doc="Record creation timestamp"
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.now,
        onupdate=datetime.now,
        nullable=False,
        doc="Last update timestamp"
    )
    
    # Relationships
    owner = relationship("SfUser", back_populates="owned_campaigns")
    target_specialties = relationship("CampaignTargetSpecialties", back_populates="campaign", cascade="all, delete-orphan")
    campaign_relationships = relationship("CampaignRelationships", back_populates="campaign")
    campaign_content = relationship("CampaignContent", back_populates="campaign")
    
    # Indexes
    __table_args__ = (
        Index("idx_campaigns_status_dates", "status", "start_date", "end_date"),
        CheckConstraint("end_date IS NULL OR end_date >= start_date", name="check_campaign_dates"),
    )


class CampaignTargetSpecialties(Base):
    """Links campaigns to multiple specialties for flexible targeting."""
    
    __tablename__ = "campaign_target_specialties"
    
    campaign_id = Column(
        UUID(as_uuid=True),
        ForeignKey("campaigns.campaign_id", ondelete="CASCADE"),
        primary_key=True,
        doc="Reference to campaign"
    )
    specialty_name = Column(
        String(255),
        primary_key=True,
        doc="The medical specialty targeted by the campaign"
    )
    created_at = Column(
        DateTime(timezone=True),
        default=datetime.now,
        nullable=False,
        doc="Record creation timestamp"
    )
    
    # Relationships
    campaign = relationship("Campaigns", back_populates="target_specialties")
    
    # Indexes
    __table_args__ = (
        Index("idx_campaign_specialties_specialty", "specialty_name"),
    )


class Relationships(Base):
    """Tracks the specific relationship a liaison has with a contact or provider group."""
    
    __tablename__ = "relationships"
    
    relationship_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        doc="Unique ID for this specific relationship instance"
    )
    user_id = Column(
        Integer,
        ForeignKey("sf_users.id"),
        nullable=False,
        index=True,
        doc="The liaison managing this relationship"
    )
    entity_type_id = Column(
        Integer,
        ForeignKey("entity_types.id"),
        nullable=False,
        index=True,
        doc="Foreign key to entity type (Contact, Provider, Site of Service)"
    )
    linked_entity_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        doc="The ID of the Contact or Provider_Group being managed"
    )
    relationship_status_id = Column(
        Integer,
        ForeignKey("relationship_status_types.id"),
        nullable=False,
        index=True,
        doc="Foreign key to relationship status type"
    )
    loyalty_status_id = Column(
        Integer,
        ForeignKey("loyalty_status_types.id"),
        index=True,
        doc="Foreign key to loyalty status type"
    )
    lead_score = Column(
        Integer,
        doc="Numerical value (1-5) indicating lead potential"
    )
    last_activity_date = Column(
        DateTime(timezone=True),
        index=True,
        doc="Date of the most recent associated activity"
    )
    next_steps = Column(
        Text,
        doc="Brief description of the immediate next actions"
    )
    engagement_frequency = Column(
        String(50),
        doc="Expected engagement frequency ('Weekly', 'Monthly', 'Quarterly')"
    )
    created_at = Column(
        DateTime(timezone=True),
        default=datetime.now,
        nullable=False,
        doc="Record creation timestamp"
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.now,
        onupdate=datetime.now,
        nullable=False,
        doc="Last update timestamp"
    )
    
    # Relationships
    user = relationship("SfUser", back_populates="managed_relationships")
    entity_type = relationship("EntityTypes", back_populates="relationships")
    relationship_status_type = relationship("RelationshipStatusTypes", back_populates="relationships")
    loyalty_status_type = relationship("LoyaltyStatusTypes", back_populates="relationships")
    campaign_relationships = relationship("CampaignRelationships", back_populates="relationship")
    history = relationship("RelationshipHistory", back_populates="related_relationship", order_by="RelationshipHistory.changed_at.desc()")
    metrics = relationship("RelationshipMetrics", back_populates="related_relationship")
    # Note: Reminders relationship is defined in the Reminders model with a complex primaryjoin
    next_best_actions = relationship("NextBestActions", back_populates="related_relationship")
    
    # Indexes
    __table_args__ = (
        Index("idx_relationships_user_entity", "user_id", "entity_type_id", "linked_entity_id"),
        Index("idx_relationships_status_loyalty", "relationship_status_id", "loyalty_status_id"),
        Index("idx_relationships_lead_score", "lead_score"),
        CheckConstraint("lead_score >= 1 AND lead_score <= 5", name="check_lead_score"),
    )


class CampaignRelationships(Base):
    """Junction table defining which relationships are part of which campaigns."""
    
    __tablename__ = "campaign_relationships"
    
    campaign_id = Column(
        UUID(as_uuid=True),
        ForeignKey("campaigns.campaign_id"),
        primary_key=True,
        doc="Reference to campaign"
    )
    relationship_id = Column(
        UUID(as_uuid=True),
        ForeignKey("relationships.relationship_id"),
        primary_key=True,
        doc="Reference to relationship"
    )
    assigned_at = Column(
        DateTime(timezone=True),
        default=datetime.now,
        nullable=False,
        doc="When this relationship was assigned to the campaign"
    )
    campaign_notes = Column(
        Text,
        doc="Specific notes relevant to this relationship within this campaign context"
    )
    
    # Relationships
    campaign = relationship("Campaigns", back_populates="campaign_relationships")
    relationship = relationship("Relationships", back_populates="campaign_relationships")
    
    # Indexes
    __table_args__ = (
        Index("idx_campaign_relationships_assigned", "assigned_at"),
    )




class ContentLibrary(Base):
    """Stores marketing materials and resources used by liaisons."""
    
    __tablename__ = "content_library"
    
    content_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        doc="Unique identifier for the content"
    )
    title = Column(
        String(255),
        nullable=False,
        index=True,
        doc="Title of the content asset"
    )
    description = Column(
        Text,
        doc="Brief description of the content"
    )
    file_path = Column(
        Text,
        nullable=False,
        doc="URL or path to the stored content file"
    )
    content_type = Column(
        String(50),
        nullable=False,
        index=True,
        doc="Type of content (e.g., 'PDF', 'Video', 'Presentation')"
    )
    tags = Column(
        ARRAY(String),
        index=True,
        doc="Array of keywords for searching"
    )
    uploaded_by_user_id = Column(
        Integer,
        ForeignKey("sf_users.id"),
        doc="User who uploaded the content"
    )
    created_at = Column(
        DateTime(timezone=True),
        default=datetime.now,
        nullable=False,
        doc="Record creation timestamp"
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.now,
        onupdate=datetime.now,
        nullable=False,
        doc="Last update timestamp"
    )
    
    # Relationships
    uploaded_by = relationship("SfUser", back_populates="uploaded_content")
    campaign_content = relationship("CampaignContent", back_populates="content")


class CampaignContent(Base):
    """Links specific content from the Content Library to Campaigns."""
    
    __tablename__ = "campaign_content"
    
    campaign_id = Column(
        UUID(as_uuid=True),
        ForeignKey("campaigns.campaign_id"),
        primary_key=True,
        doc="Reference to campaign"
    )
    content_id = Column(
        UUID(as_uuid=True),
        ForeignKey("content_library.content_id"),
        primary_key=True,
        doc="Reference to content"
    )
    
    # Relationships
    campaign = relationship("Campaigns", back_populates="campaign_content")
    content = relationship("ContentLibrary", back_populates="campaign_content")


class RelationshipHistory(Base):
    """Tracks the progression of relationships over time."""
    
    __tablename__ = "relationship_history"
    
    history_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        doc="Unique identifier for the history entry"
    )
    relationship_id = Column(
        UUID(as_uuid=True),
        ForeignKey("relationships.relationship_id"),
        nullable=False,
        index=True,
        doc="Reference to the relationship"
    )
    changed_by_user_id = Column(
        Integer,
        ForeignKey("sf_users.id"),
        nullable=False,
        doc="User who made the change"
    )
    previous_relationship_status = Column(
        String(50),
        doc="Previous relationship status"
    )
    new_relationship_status = Column(
        String(50),
        doc="New relationship status"
    )
    previous_loyalty = Column(
        String(50),
        doc="Previous loyalty status"
    )
    new_loyalty = Column(
        String(50),
        doc="New loyalty status"
    )
    change_reason = Column(
        Text,
        doc="Reason for the status change"
    )
    changed_at = Column(
        DateTime(timezone=True),
        default=datetime.now,
        nullable=False,
        index=True,
        doc="When the change occurred"
    )
    
    # Relationships
    related_relationship = relationship("Relationships", back_populates="history")
    changed_by = relationship("SfUser", foreign_keys=[changed_by_user_id])
    
    # Indexes
    __table_args__ = (
        Index("idx_relationship_history_changed", "changed_at"),
    )


class RelationshipMetrics(Base):
    """Tracks KPIs and metrics for relationships."""
    
    __tablename__ = "relationship_metrics"
    
    metric_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        doc="Unique identifier for the metric record"
    )
    relationship_id = Column(
        UUID(as_uuid=True),
        ForeignKey("relationships.relationship_id"),
        nullable=False,
        index=True,
        doc="Reference to the relationship"
    )
    metric_date = Column(
        Date,
        nullable=False,
        index=True,
        doc="Date for which metrics are calculated"
    )
    referrals_count = Column(
        Integer,
        default=0,
        doc="Number of referrals from this relationship"
    )
    meetings_count = Column(
        Integer,
        default=0,
        doc="Number of meetings held"
    )
    calls_count = Column(
        Integer,
        default=0,
        doc="Number of phone calls made"
    )
    emails_count = Column(
        Integer,
        default=0,
        doc="Number of emails sent"
    )
    engagement_score = Column(
        Numeric(5, 2),
        doc="Calculated engagement score"
    )
    calculated_at = Column(
        DateTime(timezone=True),
        default=datetime.now,
        nullable=False,
        doc="When metrics were calculated"
    )
    
    # Relationships
    related_relationship = relationship("Relationships", back_populates="metrics")
    
    # Indexes
    __table_args__ = (
        Index("idx_relationship_metrics_date", "relationship_id", "metric_date"),
        UniqueConstraint("relationship_id", "metric_date", name="uq_relationship_metric_date"),
    )


class Reminders(Base):
    """Tracks action items and reminders for relationships."""
    
    __tablename__ = "reminders"
    
    reminder_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        doc="Unique identifier for the reminder"
    )
    user_id = Column(
        Integer,
        ForeignKey("sf_users.id"),
        nullable=False,
        index=True,
        doc="User who owns the reminder"
    )
    entity_type_id = Column(
        Integer,
        ForeignKey("entity_types.id"),
        nullable=False,
        index=True,
        doc="Foreign key to entity type"
    )
    linked_entity_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        doc="ID of the linked entity"
    )
    reminder_type = Column(
        String(50),
        index=True,
        doc="Type of reminder (e.g., 'follow_up', 'meeting', 'task')"
    )
    description = Column(
        Text,
        nullable=False,
        doc="Description of what needs to be done"
    )
    due_date = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        doc="When the reminder is due"
    )
    is_completed = Column(
        Boolean,
        default=False,
        index=True,
        doc="Whether the reminder has been completed"
    )
    completed_at = Column(
        DateTime(timezone=True),
        doc="When the reminder was completed"
    )
    created_at = Column(
        DateTime(timezone=True),
        default=datetime.now,
        nullable=False,
        doc="Record creation timestamp"
    )
    
    # Relationships
    user = relationship("SfUser", back_populates="reminders")
    entity_type = relationship("EntityTypes")
    
    # Indexes
    __table_args__ = (
        Index("idx_reminders_user_due", "user_id", "due_date"),
        Index("idx_reminders_entity", "entity_type_id", "linked_entity_id"),
        Index("idx_reminders_completed", "is_completed", "due_date"),
    )


class SalesforceSync(Base):
    """Tracks synchronization between local entities and Salesforce."""
    
    __tablename__ = "salesforce_sync"
    
    sync_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        doc="Unique identifier for the sync record"
    )
    entity_type = Column(
        String(50),
        nullable=False,
        index=True,
        doc="Type of entity being synced"
    )
    local_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        doc="Local database ID"
    )
    sf_id = Column(
        String(18),
        nullable=False,
        index=True,
        doc="Salesforce ID"
    )
    last_synced_at = Column(
        DateTime(timezone=True),
        doc="Last successful sync timestamp"
    )
    sync_status = Column(
        String(50),
        doc="Status of sync ('success', 'failed', 'pending')"
    )
    error_message = Column(
        Text,
        doc="Error details if sync failed"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_salesforce_sync_entity", "entity_type", "local_id"),
        UniqueConstraint("entity_type", "local_id", name="uq_entity_local_id"),
    )


class LLMProcessingQueue(Base):
    """Queue for processing entities with LLM."""
    
    __tablename__ = "llm_processing_queue"
    
    queue_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        doc="Unique identifier for the queue entry"
    )
    entity_type_id = Column(
        Integer,
        ForeignKey("entity_types.id"),
        nullable=False,
        index=True,
        doc="Foreign key to entity type"
    )
    entity_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        doc="ID of entity to process"
    )
    processing_type = Column(
        String(50),
        nullable=False,
        index=True,
        doc="Type of processing ('summarize', 'extract_topics', 'next_actions')"
    )
    priority = Column(
        Integer,
        default=5,
        index=True,
        doc="Processing priority (1-10, lower is higher priority)"
    )
    status = Column(
        String(50),
        default='pending',
        index=True,
        doc="Processing status"
    )
    queued_at = Column(
        DateTime(timezone=True),
        default=datetime.now,
        nullable=False,
        doc="When item was queued"
    )
    processed_at = Column(
        DateTime(timezone=True),
        doc="When item was processed"
    )
    error_message = Column(
        Text,
        doc="Error details if processing failed"
    )
    
    # Relationships
    entity_type = relationship("EntityTypes")
    
    # Indexes
    __table_args__ = (
        Index("idx_llm_queue_status_priority", "status", "priority"),
        Index("idx_llm_queue_entity", "entity_type_id", "entity_id"),
    )


class NextBestActions(Base):
    """AI-generated next best actions for relationships."""
    
    __tablename__ = "next_best_actions"
    
    action_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        doc="Unique identifier for the action"
    )
    relationship_id = Column(
        UUID(as_uuid=True),
        ForeignKey("relationships.relationship_id"),
        nullable=False,
        index=True,
        doc="Reference to the relationship"
    )
    action_type = Column(
        String(50),
        nullable=False,
        index=True,
        doc="Type of recommended action"
    )
    action_description = Column(
        Text,
        nullable=False,
        doc="Detailed description of the recommended action"
    )
    confidence_score = Column(
        Numeric(3, 2),
        doc="AI confidence score (0.00-1.00)"
    )
    suggested_date = Column(
        Date,
        doc="Suggested date to take the action"
    )
    is_completed = Column(
        Boolean,
        default=False,
        index=True,
        doc="Whether the action has been completed"
    )
    generated_at = Column(
        DateTime(timezone=True),
        default=datetime.now,
        nullable=False,
        doc="When the action was generated"
    )
    expires_at = Column(
        DateTime(timezone=True),
        doc="When the recommendation expires"
    )
    
    # Relationships
    related_relationship = relationship("Relationships", back_populates="next_best_actions")
    
    # Indexes
    __table_args__ = (
        Index("idx_next_best_actions_active", "relationship_id", "is_completed", "expires_at"),
        CheckConstraint("confidence_score >= 0 AND confidence_score <= 1", name="check_confidence_score"),
    )