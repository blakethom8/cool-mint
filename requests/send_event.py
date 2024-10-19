import json
import requests
from pathlib import Path

BASE_URL = "http://localhost:8080/events"
EVENTS_DIR = Path(__file__).parent.parent / "requests/events"


def load_event(event_file: str):
    with open(EVENTS_DIR / event_file, "r") as f:
        return json.load(f)


def send_event(event_file: str):
    payload = load_event(event_file)
    response = requests.post(BASE_URL, json=payload)

    print(f"Testing {event_file}:")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")

    assert response.status_code == 202


if __name__ == "__main__":
    send_event(event_file="invoice.json")
    send_event(event_file="product.json")
    send_event(event_file="policy_question.json")
