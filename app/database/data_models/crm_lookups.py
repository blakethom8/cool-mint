import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    String,
    Integer,
    Text,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from database.session import Base

"""
CRM Lookup Tables

This module defines lookup tables for the CRM system to maintain
controlled vocabularies for various status fields.
"""


class RelationshipStatusTypes(Base):
    """Lookup table for relationship status values.
    
    Defines the valid statuses a relationship can have, providing
    controlled vocabulary and additional metadata for each status.
    """
    
    __tablename__ = "relationship_status_types"
    
    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        doc="Unique identifier for the status type"
    )
    code = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        doc="Internal code for the status (e.g., 'PROSPECTING', 'BUILDING')"
    )
    display_name = Column(
        String(100),
        nullable=False,
        doc="User-friendly display name"
    )
    description = Column(
        Text,
        doc="Detailed description of what this status means"
    )
    sort_order = Column(
        Integer,
        default=0,
        doc="Order for display in UI dropdowns"
    )
    is_active = Column(
        Boolean,
        default=True,
        index=True,
        doc="Whether this status is currently available for use"
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
    
    # Relationships (using string reference to avoid circular import)
    relationships = relationship("Relationships", back_populates="relationship_status_type", lazy="dynamic")
    
    # Indexes
    __table_args__ = (
        Index("idx_relationship_status_types_active", "is_active", "sort_order"),
    )


class LoyaltyStatusTypes(Base):
    """Lookup table for loyalty status values.
    
    Defines the valid loyalty statuses, providing controlled vocabulary
    and additional metadata like color coding for UI display.
    """
    
    __tablename__ = "loyalty_status_types"
    
    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        doc="Unique identifier for the loyalty status type"
    )
    code = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        doc="Internal code for the status (e.g., 'LOYALIST', 'MIXED')"
    )
    display_name = Column(
        String(100),
        nullable=False,
        doc="User-friendly display name"
    )
    description = Column(
        Text,
        doc="Detailed description of what this loyalty level means"
    )
    color_hex = Column(
        String(7),
        doc="Hex color code for UI display (e.g., '#00AA00' for loyalist)"
    )
    sort_order = Column(
        Integer,
        default=0,
        doc="Order for display in UI dropdowns"
    )
    is_active = Column(
        Boolean,
        default=True,
        index=True,
        doc="Whether this status is currently available for use"
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
    
    # Relationships (using string reference to avoid circular import)
    relationships = relationship("Relationships", back_populates="loyalty_status_type", lazy="dynamic")
    
    # Indexes
    __table_args__ = (
        Index("idx_loyalty_status_types_active", "is_active", "sort_order"),
    )


class EntityTypes(Base):
    """Lookup table for entity type values.
    
    Defines the valid entity types that can be linked in relationships,
    providing controlled vocabulary and user-friendly display names.
    """
    
    __tablename__ = "entity_types"
    
    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        doc="Unique identifier for the entity type"
    )
    code = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        doc="Internal code for the entity type (e.g., 'ClaimsProvider', 'SfContact')"
    )
    common_name = Column(
        String(100),
        nullable=False,
        doc="User-friendly display name (e.g., 'Leads', 'Contacts')"
    )
    description = Column(
        Text,
        doc="Detailed description of what this entity type represents"
    )
    table_name = Column(
        String(100),
        doc="Database table name where these entities are stored"
    )
    sort_order = Column(
        Integer,
        default=0,
        doc="Order for display in UI dropdowns"
    )
    is_active = Column(
        Boolean,
        default=True,
        index=True,
        doc="Whether this entity type is currently available for use"
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
    
    # Relationships (using string reference to avoid circular import)
    relationships = relationship("Relationships", back_populates="entity_type", lazy="dynamic")
    
    # Indexes
    __table_args__ = (
        Index("idx_entity_types_active", "is_active", "sort_order"),
    )