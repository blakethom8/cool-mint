from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, String, Boolean, Float, DateTime, Text, JSON, ForeignKey, Index, CheckConstraint, Integer, Date, Time
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID, JSONB
from sqlalchemy.orm import relationship

from database.session import Base


class EmailAction(Base):
    """Stores classified actions extracted from emails"""
    
    __tablename__ = "email_actions"
    
    # Primary key
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Foreign key to original email
    email_id = Column(PostgresUUID(as_uuid=True), ForeignKey("emails.id"), nullable=False)
    
    # Action classification
    action_type = Column(String(50), nullable=False)  # 'add_note', 'log_call', 'set_reminder'
    action_parameters = Column(JSONB)  # Flexible parameters specific to action type
    
    # AI reasoning and confidence
    confidence_score = Column(Float, CheckConstraint('confidence_score >= 0 AND confidence_score <= 1'))
    reasoning = Column(Text)  # Why AI chose this classification
    
    # Status tracking
    status = Column(String(20), default='pending')  # 'pending', 'approved', 'rejected', 'completed', 'failed'
    
    # Review metadata
    reviewed_at = Column(DateTime(timezone=True))
    reviewed_by = Column(String(255))  # User who reviewed
    review_notes = Column(Text)  # Any notes from reviewer
    
    # Execution tracking
    executed_at = Column(DateTime(timezone=True))
    execution_result = Column(JSONB)  # Results/errors from execution
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    email = relationship("Email", backref="actions")
    
    # Indexes
    __table_args__ = (
        Index('idx_email_actions_email_id', 'email_id'),
        Index('idx_email_actions_type', 'action_type'),
        Index('idx_email_actions_status', 'status'),
        Index('idx_email_actions_created', 'created_at'),
    )


class CallLogStaging(Base):
    """Staging table for call logs pending approval"""
    
    __tablename__ = "call_logs_staging"
    
    # Primary key
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Foreign key to email action
    email_action_id = Column(PostgresUUID(as_uuid=True), ForeignKey("email_actions.id"), nullable=False)
    
    # Call log fields (matching sf_activities structure)
    subject = Column(String(255), nullable=False)
    description = Column(Text)
    activity_date = Column(DateTime(timezone=True))
    duration_minutes = Column(Integer)
    
    # Activity classification
    mno_type = Column(String(255))  # e.g., 'MD_to_MD_Visits'
    mno_subtype = Column(String(255))  # e.g., 'MD_to_MD_w_Cedars'
    mno_setting = Column(String(255))  # e.g., 'In-Person', 'Virtual'
    
    # Participants
    contact_ids = Column(JSONB)  # Array of contact IDs/names
    primary_contact_id = Column(String(255))  # Main contact
    
    # AI suggestions vs user modifications
    suggested_values = Column(JSONB)  # Original AI suggestions
    user_modifications = Column(JSONB)  # Track what user changed
    
    # Approval tracking
    approval_status = Column(String(20), default='pending')  # 'pending', 'approved', 'rejected'
    approved_by = Column(String(255))
    approved_at = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    email_action = relationship("EmailAction", backref="call_log_staging")


class NoteStaging(Base):
    """Staging table for notes pending approval"""
    
    __tablename__ = "notes_staging"
    
    # Primary key
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Foreign key to email action
    email_action_id = Column(PostgresUUID(as_uuid=True), ForeignKey("email_actions.id"), nullable=False)
    
    # Note fields
    note_content = Column(Text, nullable=False)
    note_type = Column(String(50))  # 'general', 'meeting', 'follow_up'
    
    # Related entity (what the note is attached to)
    related_entity_type = Column(String(50))  # 'contact', 'account', 'opportunity'
    related_entity_id = Column(String(255))  # ID of the entity
    related_entity_name = Column(String(255))  # Name for display
    
    # AI suggestions vs user modifications
    suggested_values = Column(JSONB)
    user_modifications = Column(JSONB)
    
    # Approval tracking
    approval_status = Column(String(20), default='pending')
    approved_by = Column(String(255))
    approved_at = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    email_action = relationship("EmailAction", backref="note_staging")


class ReminderStaging(Base):
    """Staging table for reminders/tasks pending approval"""
    
    __tablename__ = "reminders_staging"
    
    # Primary key
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Foreign key to email action
    email_action_id = Column(PostgresUUID(as_uuid=True), ForeignKey("email_actions.id"), nullable=False)
    
    # Reminder fields
    reminder_text = Column(Text, nullable=False)
    due_date = Column(DateTime(timezone=True), nullable=False)
    priority = Column(String(20), default='normal')  # 'high', 'normal', 'low'
    
    # Assignment
    assignee = Column(String(255))  # Who should do this
    assignee_id = Column(String(255))  # User ID if applicable
    
    # Related entity
    related_entity_type = Column(String(50))
    related_entity_id = Column(String(255))
    related_entity_name = Column(String(255))
    
    # AI suggestions vs user modifications
    suggested_values = Column(JSONB)
    user_modifications = Column(JSONB)
    
    # Approval tracking
    approval_status = Column(String(20), default='pending')
    approved_by = Column(String(255))
    approved_at = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    email_action = relationship("EmailAction", backref="reminder_staging")
    
    # Indexes
    __table_args__ = (
        Index('idx_reminder_staging_due_date', 'due_date'),
    )