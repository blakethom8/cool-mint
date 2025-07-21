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
    Integer,
    ARRAY,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from database.session import Base


class ActivityBundle(Base):
    """
    Represents a collection of activities bundled together for LLM processing.
    
    This table stores user-created bundles of activities with metadata about
    the bundle including token counts and descriptive information.
    """
    
    __tablename__ = "activity_bundles"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Bundle metadata
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Activity references
    activity_ids = Column(ARRAY(String), nullable=False)  # Array of Salesforce activity IDs
    activity_count = Column(Integer, nullable=False)
    
    # Token information
    token_count = Column(Integer)  # Estimated tokens for the bundle
    
    # User tracking
    created_by = Column(String(255))  # User ID or email
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    conversations = relationship("LLMConversation", back_populates="bundle", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("idx_activity_bundles_created_by", "created_by"),
        Index("idx_activity_bundles_created_at", "created_at"),
    )


class LLMConversation(Base):
    """
    Stores conversation history with LLMs for each activity bundle.
    
    Each conversation represents a chat session with an LLM about a specific
    bundle of activities.
    """
    
    __tablename__ = "llm_conversations"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key to bundle
    bundle_id = Column(UUID(as_uuid=True), ForeignKey("activity_bundles.id"), nullable=False)
    
    # LLM configuration
    model = Column(String(100), nullable=False)  # e.g., "claude-3-5-sonnet-20241022"
    
    # Conversation data
    messages = Column(JSONB, nullable=False, default=list)  # Array of {role, content, timestamp}
    
    # Token tracking
    total_tokens_used = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    bundle = relationship("ActivityBundle", back_populates="conversations")
    saved_responses = relationship("SavedLLMResponse", back_populates="conversation", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("idx_llm_conversations_bundle_id", "bundle_id"),
        Index("idx_llm_conversations_created_at", "created_at"),
    )


class SavedLLMResponse(Base):
    """
    Stores specific LLM responses that users choose to save.
    
    Users can selectively save important responses from their conversations
    for future reference or report generation.
    """
    
    __tablename__ = "saved_llm_responses"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key to conversation
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("llm_conversations.id"), nullable=False)
    
    # Response data
    prompt = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    
    # Additional metadata  
    response_metadata = Column('metadata', JSONB)  # Can store tags, categories, etc.
    
    # User note about why this was saved
    note = Column(Text)
    
    # Timestamp
    saved_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    conversation = relationship("LLMConversation", back_populates="saved_responses")
    
    # Indexes
    __table_args__ = (
        Index("idx_saved_llm_responses_conversation_id", "conversation_id"),
        Index("idx_saved_llm_responses_saved_at", "saved_at"),
    )