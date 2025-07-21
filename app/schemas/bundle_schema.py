from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID


class BundleCreateRequest(BaseModel):
    """Request model for creating a new activity bundle."""
    
    name: str = Field(..., min_length=1, max_length=255, description="Name of the bundle")
    description: Optional[str] = Field(None, description="Description of what this bundle contains")
    activity_ids: List[str] = Field(..., min_items=1, description="List of Salesforce activity IDs to include")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Sleep Related Activities Q1 2025",
                "description": "All activities mentioning sleep issues or sleep medicine from Q1",
                "activity_ids": ["00TUJ0000156HSs2AM", "00TUJ000014o7bU2AQ"]
            }
        }


class BundleResponse(BaseModel):
    """Response model for a single activity bundle."""
    
    id: UUID
    name: str
    description: Optional[str]
    activity_ids: List[str]
    activity_count: int
    token_count: Optional[int]
    created_by: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    
    # Additional computed fields
    conversation_count: int = Field(0, description="Number of LLM conversations for this bundle")
    
    class Config:
        from_attributes = True


class BundleListResponse(BaseModel):
    """Response model for listing activity bundles."""
    
    bundles: List[BundleResponse]
    total_count: int
    page: int = 1
    page_size: int = 50
    total_pages: int = 1


class BundleDetailResponse(BaseModel):
    """Detailed response for a single bundle including activity data."""
    
    bundle: BundleResponse
    activities: List[Dict[str, Any]] = Field(
        default_factory=list, 
        description="List of activity data with LLM context"
    )
    total_tokens: int = Field(0, description="Total estimated tokens for all activities")
    
    class Config:
        json_schema_extra = {
            "example": {
                "bundle": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "name": "Sleep Related Activities",
                    "description": "Activities related to sleep medicine",
                    "activity_count": 5,
                    "token_count": 2500,
                    "created_at": "2025-01-10T10:00:00Z"
                },
                "activities": [
                    {
                        "activity_id": "00TUJ0000156HSs2AM",
                        "subject": "Office Visit",
                        "description": "Patient discussed sleep issues...",
                        "llm_context": {"contacts": [], "activity_type": "Office Visit"}
                    }
                ],
                "total_tokens": 2500
            }
        }


class BundleStatsResponse(BaseModel):
    """Response model for bundle statistics shown in the creation modal."""
    
    activity_count: int
    total_characters: int
    estimated_tokens: int
    unique_owners: List[str]
    date_range: Dict[str, Optional[str]] = Field(
        default_factory=dict,
        description="Contains 'start' and 'end' dates"
    )
    activity_types: Dict[str, int] = Field(
        default_factory=dict,
        description="Count of activities by type"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "activity_count": 25,
                "total_characters": 15000,
                "estimated_tokens": 3750,
                "unique_owners": ["Jennifer Paul", "Mark Ortgies"],
                "date_range": {
                    "start": "2025-06-01",
                    "end": "2025-07-01"
                },
                "activity_types": {
                    "Task": 20,
                    "Event": 5
                }
            }
        }


class BundleDeleteResponse(BaseModel):
    """Response model for bundle deletion."""
    
    success: bool
    message: str