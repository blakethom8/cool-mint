"""
Market Data Explorer Schema

This module defines the schema for market data exploration events.
"""

from pydantic import BaseModel, Field
from typing import Optional


class MarketDataExplorerEvent(BaseModel):
    """Schema for market data exploration events."""

    query: str = Field(
        ...,
        description="The user's natural language query about market data",
        example="What is the market size for electric vehicles in California?",
    )

    market_data: Optional[str] = Field(
        description="Market data to analyze for target identification", default=None
    )

    user_id: str = Field(
        default="anonymous", description="ID of the user making the query"
    )

    session_id: str = Field(
        default="", description="Session ID for tracking conversation context"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "query": "Show me the market trends for renewable energy in Texas",
                "user_id": "user123",
                "session_id": "session456",
            }
        }
