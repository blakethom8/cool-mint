"""Base utilities for email actions testing"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parents[3]
sys.path.insert(0, str(project_root))

from database.session import db_session
from database.data_models.email_data import Email
from database.data_models.email_actions import EmailAction, CallLogStaging


def get_sample_emails(limit=10):
    """Get sample emails from database"""
    emails = []
    for session in db_session():
        query = (
            session.query(Email)
            .filter(Email.is_forwarded == True, Email.user_instruction.isnot(None))
            .order_by(Email.received_at.desc())
            .limit(limit)
        )

        for email in query:
            emails.append(
                {
                    "id": str(email.id),
                    "subject": email.subject,
                    "from_email": email.from_email,
                    "user_instruction": email.user_instruction,
                    "content": email.conversation_for_llm or email.body_plain,
                    "received_at": email.received_at.isoformat()
                    if email.received_at
                    else None,
                }
            )
    return emails


def save_test_result(test_name, result_data):
    """Save test results for analysis"""
    results_dir = Path(__file__).parent.parent / "results"
    results_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{test_name}_{timestamp}.json"

    with open(results_dir / filename, "w") as f:
        json.dump(result_data, f, indent=2, default=str)

    return filename


def load_prompt_template(prompt_name):
    """Load a prompt template from prompts directory"""
    prompts_dir = Path(__file__).parent.parent / "prompts"
    prompt_file = prompts_dir / f"{prompt_name}.txt"

    if prompt_file.exists():
        return prompt_file.read_text()
    return None


def compare_results(expected, actual):
    """Compare expected vs actual results"""
    comparison = {"matches": {}, "mismatches": {}, "missing": {}, "extra": {}}

    for key in expected:
        if key in actual:
            if expected[key] == actual[key]:
                comparison["matches"][key] = expected[key]
            else:
                comparison["mismatches"][key] = {
                    "expected": expected[key],
                    "actual": actual[key],
                }
        else:
            comparison["missing"][key] = expected[key]

    for key in actual:
        if key not in expected:
            comparison["extra"][key] = actual[key]

    return comparison
