#!/usr/bin/env python3
"""Test log call extraction for a single email"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel
from dotenv import load_dotenv

# Add parent directories to path
import sys

sys.path.insert(0, str(Path(__file__).parents[2]))

# Try to load environment variables from multiple possible locations
env_locations = [
    ".env",  # Current directory
    "../.env",  # Parent directory
    "../../.env",  # Root directory
    "../../../.env",  # Project root directory
    "../../../app/.env",  # App directory
    "../../app/.env",  # Alternative app directory path
]

env_loaded = False
for env_path in env_locations:
    if Path(env_path).exists():
        load_dotenv(env_path)
        print(f"✅ Loaded environment variables from {env_path}")
        env_loaded = True
        break

if not env_loaded:
    print("❌ No .env file found. Please create one with your ANTHROPIC_API_KEY")
    print("Possible locations to place your .env file:")
    for loc in env_locations:
        print(f"- {Path(loc).absolute()}")

# Verify Anthropic API key is available
if not os.getenv("ANTHROPIC_API_KEY"):
    print("❌ ANTHROPIC_API_KEY not found in environment variables")
    print("Please add ANTHROPIC_API_KEY=your-key-here to your .env file")
    if not env_loaded:
        exit(1)

# Configuration - Set your email ID and prompt here
EMAIL_ID = "123456"  # Change this to test different emails
SYSTEM_PROMPT = """You are extracting information to log a call, meeting, or activity.

Extract the following information:
1. **Subject**: Brief title for the activity (e.g., "MD-to-MD Lunch with Dr. McDonald")
2. **Description**: Detailed notes about what was discussed
3. **Participants**: All people involved (extract names and roles)
4. **Date**: When the activity occurred (if mentioned)
5. **Activity Type**: Categorize the activity type:
   - MD_to_MD_Visits: Direct physician-to-physician interactions and meetings
   - BD_Outreach: Physician liaison engagement with other stakeholders
   - Events: Group gatherings and educational sessions
   - Planning_Management: Internal planning and coordination
   - Other: General activities not fitting above categories

6. **Setting**: In-person, Virtual, Phone, etc.
7. **Key Topics**: List of key topics discussed
8. **Follow-up Items**: List of follow-up items mentioned

For MD-to-MD activities:
- Always include "MD-to-MD" in the subject
- Note which physicians were involved
- Capture key discussion points

Only capture information that is provided by the user or in the email thread. To not try to make inferences or assumptions for information that is not shared. """


class CallLogExtractionOutput(BaseModel):
    """Output schema for call log extraction - matches production node"""

    subject: str = Field(..., description="Subject/title for the activity")
    description: str = Field(..., description="Detailed description of the activity")
    participants: List[dict] = Field(
        ..., description="List of participants with names and roles"
    )
    activity_date: Optional[str] = Field(None, description="When the activity occurred")
    activity_type: str = Field(
        ...,
        description="Type of activity (MD_to_MD_Visits, BD_Outreach, Events, Planning_Management, Other)",
    )
    meeting_setting: str = Field("In-Person", description="In-Person, Virtual, Phone")
    key_topics: List[str] = Field(
        default_factory=list, description="Key topics discussed"
    )
    follow_up_items: List[str] = Field(
        default_factory=list, description="Follow-up items mentioned"
    )

    # Optional fields
    is_md_to_md: bool = Field(False, description="Whether this is an MD-to-MD activity")


def find_email_by_id(email_id: str) -> Dict:
    """Find a specific email in the test data by ID"""
    test_data_path = Path(__file__).parent / "test_data" / "emails_with_actions.json"

    if not test_data_path.exists():
        raise FileNotFoundError(f"Test data not found at {test_data_path}")

    with open(test_data_path) as f:
        test_cases = json.load(f)

    # Find the email with matching ID
    for test_case in test_cases:
        if test_case.get("email", {}).get("id") == email_id:
            return test_case

    raise ValueError(f"Email with ID '{email_id}' not found in test data")


def extract_call_log_data(email_id: str, system_prompt: str) -> CallLogExtractionOutput:
    """Extract call log data from a single email using the specified prompt"""

    # Load the specific email
    test_case = find_email_by_id(email_id)

    # Extract email content and user instruction
    # Handle both test data structure and real database fields
    email_content = test_case.get("email", {}).get("content", "")
    if not email_content:
        # Fall back to database fields if content field doesn't exist
        body = test_case.get("email", {}).get("body", "")
        body_plain = test_case.get("email", {}).get("body_plain", "")
        clean_body = test_case.get("email", {}).get("clean_body", "")
        extracted_thread = test_case.get("email", {}).get("extracted_thread", "")

        # Use the best available content field
        email_content = clean_body or body_plain or body or extracted_thread

    user_instruction = test_case.get("email", {}).get("user_instruction", "")

    # Get email metadata
    from_email = test_case.get("email", {}).get("from_email", "")
    subject = test_case.get("email", {}).get("subject", "")

    if not email_content and not user_instruction:
        raise ValueError(f"Email {email_id} has no content or user instruction")

    # Configure agent with Anthropic model
    model = AnthropicModel("claude-3-5-haiku-20241022")
    agent = Agent(
        system_prompt=system_prompt, result_type=CallLogExtractionOutput, model=model
    )

    # Prepare the user prompt (matching production node format)
    user_prompt = f"""Extract call/meeting information from this email:

From: {from_email}
Subject: {subject}

User Instruction: {user_instruction}

Email Content:
{email_content}

Extract all relevant information for logging this activity."""

    # Run extraction (assuming Jupyter notebook environment)
    try:
        import nest_asyncio

        nest_asyncio.apply()
    except ImportError:
        # Install nest_asyncio if not available
        print("Installing nest_asyncio for Jupyter compatibility...")
        import subprocess
        import sys

        subprocess.check_call([sys.executable, "-m", "pip", "install", "nest_asyncio"])
        import nest_asyncio

        nest_asyncio.apply()

    result = agent.run_sync(user_prompt=user_prompt)
    return result.output


def main():
    """Main function to test call log extraction for a single email"""
    print(f"Testing call log extraction for email: {EMAIL_ID}")
    print("=" * 50)

    try:
        # Run extraction
        result = extract_call_log_data(EMAIL_ID, SYSTEM_PROMPT)

        # Display results in a structured format
        print(f"Subject: {result.subject}")
        print(f"Description: {result.description}")
        print(f"Activity Type: {result.activity_type}")
        print(f"Meeting Setting: {result.meeting_setting}")
        print(f"Is MD-to-MD: {result.is_md_to_md}")
        print(f"Activity Date: {result.activity_date}")

        print("\nParticipants:")
        for i, participant in enumerate(result.participants, 1):
            print(f"  {i}. {participant}")

        print("\nKey Topics:")
        for topic in result.key_topics:
            print(f"  - {topic}")

        print("\nFollow-up Items:")
        for item in result.follow_up_items:
            print(f"  - {item}")

        # Show staging area data structure (what would be saved)
        print("\n" + "=" * 50)
        print("STAGING AREA DATA STRUCTURE:")
        print("=" * 50)

        # Determine MNO type and subtype (matching production logic)
        if result.is_md_to_md:
            mno_type = "MD_to_MD_Visits"
            mno_subtype = (
                "MD_to_MD_w_Cedars"  # Could be more sophisticated based on content
            )
        else:
            mno_type = "BD_Outreach"
            mno_subtype = "General_Meeting"

        staging_data = {
            "subject": result.subject,
            "description": result.description,
            "participants": result.participants,
            "activity_date": result.activity_date,
            "activity_type": result.activity_type,
            "meeting_setting": result.meeting_setting,
            "is_md_to_md": result.is_md_to_md,
            "key_topics": result.key_topics,
            "follow_up_items": result.follow_up_items,
            "mno_type": mno_type,
            "mno_subtype": mno_subtype,
            "mno_setting": result.meeting_setting,
        }

        print(json.dumps(staging_data, indent=2, default=str))

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
