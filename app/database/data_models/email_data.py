from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, String, Boolean, Integer, DateTime, Text, JSON, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import relationship

from database.session import Base


class Email(Base):
    """Stores email messages received from Nylas webhooks"""
    
    __tablename__ = "emails"
    
    # Primary key
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Nylas identifiers
    nylas_id = Column(String(255), unique=True, nullable=False, index=True)
    grant_id = Column(String(255), nullable=False, index=True)
    thread_id = Column(String(255), nullable=False, index=True)
    
    # Email metadata
    subject = Column(Text, nullable=True)
    snippet = Column(Text, nullable=True)
    date = Column(Integer, nullable=False)  # Unix timestamp
    received_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
    # Email participants
    from_email = Column(String(255), nullable=True, index=True)
    from_name = Column(String(255), nullable=True)
    to_emails = Column(JSON, nullable=True)  # List of email addresses
    cc_emails = Column(JSON, nullable=True)  # List of email addresses
    bcc_emails = Column(JSON, nullable=True)  # List of email addresses
    
    # Email content
    body = Column(Text, nullable=True)
    body_plain = Column(Text, nullable=True)  # Plain text version if available
    
    # Email status
    unread = Column(Boolean, default=True)
    starred = Column(Boolean, default=False)
    
    # Processing status
    processed = Column(Boolean, default=False, index=True)
    processing_status = Column(String(50), nullable=True)  # e.g., 'pending', 'classified', 'completed', 'error'
    classification = Column(String(50), nullable=True)  # e.g., 'spam', 'invoice', 'general', etc.
    
    # Metadata
    folders = Column(JSON, nullable=True)  # List of folder IDs
    labels = Column(JSON, nullable=True)  # List of label IDs
    attachments_count = Column(Integer, default=0)
    has_attachments = Column(Boolean, default=False)
    
    # Raw data storage
    raw_webhook_data = Column(JSON, nullable=True)  # Store complete webhook payload
    
    # Enhanced email content fields
    clean_body = Column(Text, nullable=True)  # Cleaned version of email content
    user_instruction = Column(Text, nullable=True)  # Sales rep's request (top of forwarded email)
    extracted_thread = Column(Text, nullable=True)  # The forwarded conversation content
    
    # Email metadata for better processing
    headers = Column(JSON, nullable=True)  # Email headers for metadata
    message_id = Column(String(255), nullable=True, index=True)  # Unique message identifier
    in_reply_to = Column(String(255), nullable=True)  # Reference to parent message
    is_forwarded = Column(Boolean, default=False)  # Auto-detect forwarded emails
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    attachments = relationship("EmailAttachment", back_populates="email", cascade="all, delete-orphan")
    activities = relationship("EmailActivity", back_populates="email", cascade="all, delete-orphan")
    parsed_data = relationship("EmailParsed", back_populates="email", uselist=False, cascade="all, delete-orphan")
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_emails_date', 'date'),
        Index('idx_emails_from_subject', 'from_email', 'subject'),
        Index('idx_emails_processing', 'processed', 'processing_status'),
    )
    
    @property
    def is_forwarded_email(self):
        """Detect if email is forwarded based on subject and content markers"""
        if self.subject:
            forwarding_markers = ['fwd:', 'fw:', 'forwarded:', 'fwd :', 'fw :']
            if any(marker in self.subject.lower() for marker in forwarding_markers):
                return True
        
        # Check body for forwarding markers
        if self.body_plain or self.body:
            content = self.body_plain or self.body
            forwarding_patterns = [
                '---------- forwarded message',
                '-------- original message',
                'begin forwarded message',
                '>>> begin forwarded'
            ]
            if any(pattern in content.lower() for pattern in forwarding_patterns):
                return True
        
        return False
    
    @property
    def conversation_for_llm(self):
        """Return the best available conversation context for LLM processing"""
        if self.user_instruction and self.extracted_thread:
            return f"User Request:\n{self.user_instruction}\n\nEmail Thread:\n{self.extracted_thread}"
        elif self.clean_body:
            return self.clean_body
        elif self.body_plain:
            return self.body_plain
        else:
            return self.body
    
    @property
    def has_user_instruction(self):
        """Check if email has a user instruction (typical for forwarded emails)"""
        return bool(self.user_instruction)


class EmailAttachment(Base):
    """Stores email attachment metadata"""
    
    __tablename__ = "email_attachments"
    
    # Primary key
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Foreign key to email
    email_id = Column(PostgresUUID(as_uuid=True), ForeignKey("emails.id"), nullable=False)
    
    # Nylas identifiers
    nylas_id = Column(String(255), nullable=False)
    grant_id = Column(String(255), nullable=False)
    
    # Attachment metadata
    filename = Column(String(500), nullable=False)
    content_type = Column(String(255), nullable=False)
    size = Column(Integer, nullable=False)  # Size in bytes
    content_id = Column(String(255), nullable=True)
    content_disposition = Column(String(50), nullable=True)
    is_inline = Column(Boolean, default=False)
    
    # Storage information
    storage_path = Column(String(500), nullable=True)  # Local storage path if downloaded
    downloaded = Column(Boolean, default=False)
    download_date = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
    # Relationships
    email = relationship("Email", back_populates="attachments")


class EmailActivity(Base):
    """Tracks actions taken on emails"""
    
    __tablename__ = "email_activities"
    
    # Primary key
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Foreign key to email
    email_id = Column(PostgresUUID(as_uuid=True), ForeignKey("emails.id"), nullable=False)
    
    # Activity details
    activity_type = Column(String(50), nullable=False)  # e.g., 'replied', 'forwarded', 'archived', 'deleted'
    activity_data = Column(JSON, nullable=True)  # Additional activity-specific data
    performed_by = Column(String(255), nullable=True)  # System or user identifier
    
    # Timestamps
    performed_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
    # Relationships
    email = relationship("Email", back_populates="activities")