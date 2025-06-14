"""
Market Data Explorer Event Schema

Defines the input schema for market data exploration queries.
"""

from pydantic import BaseModel, Field


class MarketDataExplorerEvent(BaseModel):
    """Event schema for market data exploration queries."""

    query: str = Field(
        ...,
        description="The user's natural language query about market data",
        example="What is the market size for electric vehicles in California?",
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
