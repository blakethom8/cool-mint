import json
from pathlib import Path
from typing import Dict


EVENTS_DIR = Path(__file__).parent.parent.parent / "requests/events"


class EventLoader:
    @staticmethod
    def load_event(event_key: str) -> Dict:
        file_path = EVENTS_DIR / f"{event_key}.json"

        try:
            with open(file_path, "r") as f:
                event_data = json.load(f)
                return event_data
        except json.JSONDecodeError as e:
            raise ValueError(f"Error parsing JSON file {file_path}: {e}")
        except IOError as e:
            raise ValueError(f"Event '{event_key}.json' not found in events folder")

    @staticmethod
    def load_event_payload(event_key: str) -> Dict:
        full_event = EventLoader.load_event(event_key)
        try:
            return full_event["data"]["object"]
        except KeyError:
            # Or handle more gracefully, maybe raise a custom error
            raise ValueError(
                f"Event {event_key} does not have the expected 'data.object' structure."
            )
