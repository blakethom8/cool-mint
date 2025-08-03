#!/usr/bin/env python3
"""Test intent classification for a single email"""

import os
import json
from pathlib import Path
from typing import Dict, List
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
EMAIL_ID = "12345"  # Change this to test different emails
SYSTEM_PROMPT = """You are an AI assistant for a medical CRM system that classifies physician liaison emails.

Analyze the user's instruction and email content to determine the PRIMARY action requested:

1. **log_call**: Log any physician interaction, meeting, or MD-to-MD activity
   - Key indicators: "log", "had a meeting", "met with", "MD-to-MD", "lunch", "call", "discussion"
   - Medical context: physician names, hospital references, clinical discussions
   
2. **add_note**: Capture information or observations without logging an activity
   - Key indicators: "note", "capture", "document", "record" (without meeting context)
   - General information that needs to be saved
   
3. **set_reminder**: Create a follow-up task or reminder
   - Key indicators: "remind", "follow up", "check back", time references like "in X days"
   
4. **unknown**: When the intent is unclear or doesn't match above categories

Focus on the USER INSTRUCTION first, then use email content for context.
Look for medical/clinical context that suggests physician interactions."""


class IntentClassificationOutput(BaseModel):
    """Output schema for intent classification"""

    action_type: str = Field(
        ..., description="One of: add_note, log_call, set_reminder, unknown"
    )
    confidence_score: float = Field(
        ..., description="Confidence in classification (0-1)"
    )
    reasoning: str = Field(
        ..., description="Explanation of why this classification was chosen"
    )
    keywords_found: List[str] = Field(
        default_factory=list, description="Key phrases that influenced the decision"
    )


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


def classify_single_email(
    email_id: str, system_prompt: str
) -> IntentClassificationOutput:
    """Classify a single email using the specified prompt"""

    # Load the specific email
    test_case = find_email_by_id(email_id)

    # Extract email content and user instruction
    email_content = test_case.get("email", {}).get("content", "")
    user_instruction = test_case.get("email", {}).get("user_instruction", "")

    if not email_content and not user_instruction:
        raise ValueError(f"Email {email_id} has no content or user instruction")

    # Configure agent with Anthropic model
    model = AnthropicModel("claude-3-5-haiku-20241022")
    agent = Agent(
        system_prompt=system_prompt, result_type=IntentClassificationOutput, model=model
    )

    # Prepare the user prompt
    user_prompt = f"""Classify this email request:

User Instruction: {user_instruction}

Email Content:
{email_content}

Determine the primary action being requested."""

    # Run classification (assuming Jupyter notebook environment)
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
    """Main function to test a single email classification"""
    print(f"Testing intent classification for email: {EMAIL_ID}")
    print("=" * 50)

    try:
        # Run classification
        result = classify_single_email(EMAIL_ID, SYSTEM_PROMPT)

        # Display results
        print(f"Action Type: {result.action_type}")
        print(f"Confidence: {result.confidence_score:.2f}")
        print(f"Reasoning: {result.reasoning}")
        print(f"Keywords Found: {', '.join(result.keywords_found)}")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
