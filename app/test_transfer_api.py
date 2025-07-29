#!/usr/bin/env python3
"""Test the transfer APIs"""

import requests
import json
from datetime import datetime

# Test data for call log transfer
test_transfer = {
    "user_id": "123",
    "final_values": {
        "subject": "MD-to-MD Lunch with Dr. Smith",
        "description": "Discussed Epic integration challenges and patient referral patterns",
        "activity_date": datetime.now().isoformat(),
        "mno_type": "MD_to_MD_Visits", 
        "mno_subtype": "MD_to_MD_w_Cedars",
        "mno_setting": "In-Person",
        "contact_ids": ["Dr. Smith", "Dr. Johnson"],
        "priority": "High"
    },
    "additional_data": {
        "user_name": "Blake Thomson"
    }
}

# You'll need to replace this with an actual staging_id from your database
staging_id = "REPLACE_WITH_ACTUAL_STAGING_ID"

url = f"http://localhost:8080/api/email-actions/call-logs/{staging_id}/transfer"

print(f"Testing transfer API: {url}")
print(f"Request data: {json.dumps(test_transfer, indent=2)}")

try:
    response = requests.post(url, json=test_transfer)
    print(f"\nResponse status: {response.status_code}")
    print(f"Response data: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")