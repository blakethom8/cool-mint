from datetime import datetime
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field
from uuid import UUID


class LLMMessage(BaseModel):
    """Individual message in an LLM conversation."""
    
    role: Literal["system", "user", "assistant"] = Field(..., description="Role of the message sender")
    content: str = Field(..., description="Content of the message")
    timestamp: Optional[datetime] = Field(None, description="When the message was sent")
    tokens: Optional[int] = Field(None, description="Token count for this message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "role": "user",
                "content": "Can you summarize the key activities related to sleep medicine?",
                "timestamp": "2025-01-10T10:00:00Z",
                "tokens": 15
            }
        }


class LLMMessageRequest(BaseModel):
    """Request to send a message to the LLM."""
    
    message: str = Field(..., min_length=1, description="User's message to the LLM")
    model: Optional[str] = Field("claude-3-5-sonnet-20241022", description="LLM model to use")
    temperature: Optional[float] = Field(0.7, ge=0, le=2, description="Temperature for response generation")
    max_tokens: Optional[int] = Field(None, ge=1, le=16384, description="Maximum tokens in response")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "What are the success stories from these activities?",
                "model": "claude-3-5-sonnet-20241022",
                "temperature": 0.7
            }
        }


class ConversationCreateRequest(BaseModel):
    """Request to create a new LLM conversation."""
    
    bundle_id: UUID = Field(..., description="ID of the activity bundle to analyze")
    model: str = Field("claude-3-5-sonnet-20241022", description="LLM model to use")
    system_prompt: Optional[str] = Field(
        None, 
        description="Custom system prompt for the conversation"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "bundle_id": "123e4567-e89b-12d3-a456-426614174000",
                "model": "claude-3-5-sonnet-20241022",
                "system_prompt": "You are analyzing medical activities. Focus on clinical outcomes."
            }
        }


class ConversationResponse(BaseModel):
    """Response model for an LLM conversation."""
    
    id: UUID
    bundle_id: UUID
    model: str
    messages: List[LLMMessage]
    total_tokens_used: int
    created_at: datetime
    updated_at: Optional[datetime]
    
    # Additional computed fields
    message_count: int = Field(0, description="Total number of messages")
    saved_responses_count: int = Field(0, description="Number of saved responses")
    
    class Config:
        from_attributes = True


class ConversationListResponse(BaseModel):
    """Response for listing conversations."""
    
    conversations: List[ConversationResponse]
    total_count: int


class SaveResponseRequest(BaseModel):
    """Request to save a specific LLM response."""
    
    conversation_id: UUID = Field(..., description="ID of the conversation")
    prompt: str = Field(..., description="The prompt that generated this response")
    response: str = Field(..., description="The LLM response to save")
    note: Optional[str] = Field(None, description="User note about why this was saved")
    response_metadata: Optional[Dict[str, Any]] = Field(
        None, 
        description="Additional metadata like tags or categories"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
                "prompt": "What are the key success metrics?",
                "response": "Based on the activities, the key success metrics are...",
                "note": "Important for quarterly report",
                "metadata": {
                    "tags": ["success", "metrics", "Q1"],
                    "category": "reporting"
                }
            }
        }


class SavedResponseItem(BaseModel):
    """Model for a saved LLM response."""
    
    id: UUID
    conversation_id: UUID
    prompt: str
    response: str
    note: Optional[str]
    response_metadata: Optional[Dict[str, Any]]
    saved_at: datetime
    
    class Config:
        from_attributes = True


class SavedResponsesResponse(BaseModel):
    """Response for listing saved responses."""
    
    responses: List[SavedResponseItem]
    total_count: int


class LLMStreamResponse(BaseModel):
    """Response model for streaming LLM responses."""
    
    chunk: str = Field(..., description="Text chunk from the LLM")
    done: bool = Field(False, description="Whether the response is complete")
    tokens_used: Optional[int] = Field(None, description="Tokens used so far")
    error: Optional[str] = Field(None, description="Error message if any")


class PredefinedPrompt(BaseModel):
    """Model for predefined prompts."""
    
    id: str
    category: str
    title: str
    prompt: str
    description: Optional[str]
    variables: Optional[List[str]] = Field(
        None, 
        description="Variables that can be replaced in the prompt"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "success-stories",
                "category": "Analysis",
                "title": "Extract Success Stories",
                "prompt": "Please identify and summarize all success stories from these activities...",
                "description": "Finds positive outcomes and achievements",
                "variables": []
            }
        }


class PredefinedPromptsResponse(BaseModel):
    """Response for listing predefined prompts."""
    
    prompts: List[PredefinedPrompt]
    categories: List[str]