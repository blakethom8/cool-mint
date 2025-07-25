from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, String, Boolean, Integer, DateTime, Text, JSON, ForeignKey, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID, JSONB
from sqlalchemy.orm import relationship

from database.session import Base


class EmailParsed(Base):
    """Stores parsed and extracted data from emails"""
    
    __tablename__ = "emails_parsed"
    
    # Primary key
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Foreign key to original email
    email_id = Column(PostgresUUID(as_uuid=True), ForeignKey("emails.id"), unique=True, nullable=False)
    
    # Parsing metadata
    parsed_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    parser_version = Column(String(50), default="v1.0")
    model_used = Column(String(100))  # 'gpt-4', 'claude-3', etc.
    
    # Email classification
    is_forwarded = Column(Boolean, default=False)
    is_action_required = Column(Boolean, default=False)
    email_type = Column(String(100))  # 'forwarded_request', 'direct_email', 'auto_reply'
    
    # User request (for forwarded emails)
    user_request = Column(Text)  # Raw request: "log MD-to-MD activity..."
    request_intents = Column(JSONB)  # ["log_activity", "capture_notes"]
    
    # Forwarded email metadata
    forwarded_from = Column(JSONB)  # {email, name, date, subject}
    forwarded_thread_id = Column(String(255))  # Original thread ID if extractable
    
    # Extracted entities
    people = Column(JSONB)  # [{name, email, role, organization, confidence}]
    organizations = Column(JSONB)  # [{name, type, confidence}]
    dates_mentioned = Column(JSONB)  # [{date, context, type: 'meeting'/'deadline'}]
    locations = Column(JSONB)  # [{place, address, type}]
    
    # Structured content
    meeting_info = Column(JSONB)  # {type, attendees, date, topics, location}
    action_items = Column(JSONB)  # [{task, deadline, assignee, priority}]
    key_topics = Column(JSONB)  # ["Epic integration", "Patient sharing"]
    
    # Thread context
    thread_summary = Column(Text)
    thread_participants = Column(JSONB)  # All unique participants in thread
    thread_message_count = Column(Integer)
    
    # Sentiment & Priority
    sentiment = Column(String(50))  # 'positive', 'neutral', 'negative'
    urgency_score = Column(Integer, CheckConstraint('urgency_score >= 0 AND urgency_score <= 10'))
    
    # Name resolution (for CRM matching)
    entity_mappings = Column(JSONB)  # {"Dr. McDonald": "devon_mcdonald_123"}
    
    # Relationships
    email = relationship("Email", back_populates="parsed_data")
    
    # Indexes (defined at table level in migration)
    __table_args__ = (
        Index('idx_parsed_email_id', 'email_id'),
        Index('idx_parsed_type', 'email_type'),
        Index('idx_parsed_action_required', 'is_action_required'),
        Index('idx_parsed_urgency', urgency_score.desc()),
    )