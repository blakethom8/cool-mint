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
    Index,
    UniqueConstraint,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from database.session import Base

# Import SfUser for relationships
from database.data_models.salesforce_data import SfUser

"""
CRM General Database Models

This module defines general-purpose models for the CRM system including:
1. Notes: Detailed notes about various entities optimized for LLM processing
2. Tags: Flexible labeling system for entities
3. Entity_Tags: Junction table for applying tags to any entity
"""


class Notes(Base):
    """Stores detailed, context-rich notes about various entities.
    
    This table is specifically designed for LLM processing and insights generation.
    Notes can be attached to any entity type in the system and include both raw
    content and LLM-processed metadata.
    """
    
    __tablename__ = "notes"
    
    note_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        doc="Unique identifier for the note"
    )
    user_id = Column(
        Integer,
        ForeignKey("sf_users.id"),
        nullable=False,
        index=True,
        doc="The user who created the note"
    )
    linked_entity_type = Column(
        String(50),
        nullable=False,
        index=True,
        doc="Type of entity the note is associated with"
    )
    linked_entity_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        doc="The ID of the entity the note is linked to"
    )
    note_content = Column(
        Text,
        nullable=False,
        doc="The raw, unstructured textual content of the note"
    )
    llm_summary = Column(
        Text,
        doc="LLM-generated concise summary of the note"
    )
    llm_topics = Column(
        JSONB,
        doc="LLM-extracted key topics (e.g., ['referral', 'patient care'])"
    )
    llm_sentiment = Column(
        String(50),
        doc="LLM-detected sentiment (e.g., 'Positive', 'Negative', 'Neutral')"
    )
    llm_processed_at = Column(
        DateTime(timezone=True),
        doc="Timestamp of the last LLM processing"
    )
    llm_processing_status = Column(
        String(50),
        default='Pending',
        index=True,
        doc="Status of LLM processing ('Pending', 'Processed', 'Failed')"
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
    user = relationship("SfUser", back_populates="notes")
    
    # Indexes for common queries
    __table_args__ = (
        Index("idx_notes_entity", "linked_entity_type", "linked_entity_id"),
        Index("idx_notes_user_created", "user_id", "created_at"),
        Index("idx_notes_llm_status", "llm_processing_status"),
        Index("idx_notes_created", "created_at"),
        CheckConstraint(
            "linked_entity_type IN ('Contact', 'ProviderGroup', 'Relationship', 'Campaign', 'Activity')",
            name="check_note_entity_type"
        ),
    )


class Tags(Base):
    """Flexible labeling system for organizing and categorizing entities.
    
    Tags can be created by users and applied to various entity types
    throughout the system for improved organization and searchability.
    """
    
    __tablename__ = "tags"
    
    tag_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        doc="Unique identifier for the tag"
    )
    tag_name = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        doc="Unique name of the tag"
    )
    tag_type = Column(
        String(50),
        index=True,
        doc="Type/category of tag (e.g., 'relationship', 'campaign', 'general')"
    )
    description = Column(
        Text,
        doc="Description of what this tag represents"
    )
    color_hex = Column(
        String(7),
        doc="Hex color code for UI display (e.g., '#FF5733')"
    )
    created_by_user_id = Column(
        Integer,
        ForeignKey("sf_users.id"),
        nullable=False,
        doc="User who created the tag"
    )
    is_active = Column(
        Boolean,
        default=True,
        index=True,
        doc="Whether the tag is currently active/available for use"
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
    created_by = relationship("SfUser", back_populates="created_tags")
    entity_tags = relationship("EntityTags", back_populates="tag", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("idx_tags_type_active", "tag_type", "is_active"),
        CheckConstraint(
            "color_hex IS NULL OR color_hex ~ '^#[0-9A-Fa-f]{6}$'",
            name="check_valid_hex_color"
        ),
    )


class EntityTags(Base):
    """Junction table for applying tags to any entity in the system.
    
    This table enables a many-to-many relationship between tags and
    various entity types, providing flexible categorization capabilities.
    """
    
    __tablename__ = "entity_tags"
    
    entity_type = Column(
        String(50),
        primary_key=True,
        doc="Type of entity being tagged"
    )
    entity_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        doc="ID of the entity being tagged"
    )
    tag_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tags.tag_id", ondelete="CASCADE"),
        primary_key=True,
        doc="Reference to the tag"
    )
    tagged_by_user_id = Column(
        Integer,
        ForeignKey("sf_users.id"),
        nullable=False,
        doc="User who applied the tag"
    )
    tagged_at = Column(
        DateTime(timezone=True),
        default=datetime.now,
        nullable=False,
        doc="When the tag was applied"
    )
    
    # Relationships
    tag = relationship("Tags", back_populates="entity_tags")
    tagged_by = relationship("SfUser", back_populates="tagged_entities")
    
    # Indexes
    __table_args__ = (
        Index("idx_entity_tags_entity", "entity_type", "entity_id"),
        Index("idx_entity_tags_tag", "tag_id"),
        Index("idx_entity_tags_user", "tagged_by_user_id"),
        CheckConstraint(
            "entity_type IN ('Contact', 'ProviderGroup', 'Relationship', 'Campaign', 'Activity', 'Content')",
            name="check_tag_entity_type"
        ),
    )