import json
import logging
from pathlib import Path
from typing import Dict, Any, List
from api.event_schema import EventSchema

logging.basicConfig(level=logging.INFO)

EVENTS_DIR = Path(__file__).parent.parent.parent / "requests/events"


class EventFactory:
    @staticmethod
    def create_event(event_key: str) -> EventSchema:
        events = EventFactory._load_all_events()
        if event_key not in events:
            logging.error(f"Event '{event_key}.json' not found in events folder")
            raise ValueError(f"Event '{event_key}.json' not found in events folder")

        event_data = events[event_key]
        logging.info(f"Created event: {event_key}")
        return EventSchema(**event_data)

    @staticmethod
    def get_all_event_keys() -> List[str]:
        return [file.stem for file in EVENTS_DIR.glob("*.json")]

    @staticmethod
    def _load_all_events() -> Dict[str, Any]:
        events = {}
        for json_file in EVENTS_DIR.glob("*.json"):
            event_name = json_file.stem
            event_data = EventFactory._load_json_file(json_file)
            if event_data:
                events[event_name] = event_data
        return events

    @staticmethod
    def _load_json_file(file_path: Path) -> Dict[str, Any]:
        try:
            with open(file_path, "r") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logging.error(f"Error parsing JSON file {file_path}: {e}")
            return {}
        except IOError as e:
            logging.error(f"Error reading file {file_path}: {e}")
            return {}
