"""
Monthly Activity Summary Schema

This module defines the Pydantic schemas for the monthly activity summary workflow.
"""

from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, Field


class MonthlyActivitySummaryEvent(BaseModel):
    """Event schema for monthly activity summary requests."""

    user_id: str = Field(
        description="Salesforce user ID to generate summary for",
        min_length=15,
        max_length=18,
    )

    start_date: Optional[date] = Field(
        default=None,
        description="Start date for the summary period (defaults to 1 month ago)",
    )

    end_date: Optional[date] = Field(
        default=None, description="End date for the summary period (defaults to today)"
    )

    request_type: str = Field(
        default="monthly_summary", description="Type of summary request"
    )

    session_id: Optional[str] = Field(
        default=None, description="Session ID for tracking purposes"
    )

    metadata: Optional[dict] = Field(
        default_factory=dict, description="Additional metadata for the request"
    )
