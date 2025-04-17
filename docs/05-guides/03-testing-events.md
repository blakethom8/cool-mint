# Event Testing System

The GenAI Launchpad provides a comprehensive event testing system that enables developers to test workflows both locally and through the API. This system consists of two main components: the EventFactory for local testing and a send_event utility for API testing.

## Event Storage

Events are stored as JSON files in the `requests/events` directory:

```
requests/
└── events/
    ├── support_ticket.json
    ├── content_analysis.json
    └── translation_request.json
```

Example event JSON:
```json
{
    "type": "support_ticket",
    "data": {
        "sender": "customer@example.com",
        "subject": "Login Issue",
        "body": "I can't access my account...",
        "priority": "high"
    }
}
```

## Event Factory

The EventFactory provides a convenient way to load and create event objects during local development and testing:

```python
from playground.utils import EventFactory

# Create event from JSON file
event = EventFactory.create_event("support_ticket")

# Get list of available events
available_events = EventFactory.get_all_event_keys()
```

### Implementation Details

The EventFactory implements a robust loading system:

```python
class EventFactory:
    @staticmethod
    def create_event(event_key: str) -> EventSchema:
        events = EventFactory._load_all_events()
        if event_key not in events:
            raise ValueError(f"Event '{event_key}.json' not found")
            
        event_data = events[event_key]
        return EventSchema(**event_data)
```

## Local Workflow Testing

You can use the EventFactory to test workflows directly without going through the API:

```python
# Test script example
from playground.utils import EventFactory
from workflows.support import SupportWorkflow


def test_support_workflow():
    # Create test event
    event = EventFactory.create_event("support_ticket")

    # Initialize and run workflow
    workflow = SupportWorkflow()
    result = workflow.run(event)

    # Validate results
    assert result.nodes["AnalyzeNode"]["intent"] == "account_access"
    assert result.nodes["RouterNode"]["next_node"] == "UrgentResponse"
```

## API Testing with send_event.py

The send_event utility allows you to test the complete system flow:

```python
# Send event through API
python requests/send_event.py support_ticket.json
```

Implementation:
```python
def send_event(event_file: str):
    """Send event to the API endpoint for processing."""
    payload = load_event(event_file)
    response = requests.post(BASE_URL, json=payload)
    
    print(f"Testing {event_file}:")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
```

The results will be stored in the database for you to review. Please note that the Docker containers should be running in order for this to work.

## Development Workflow

1. **Create Test Events**:
```json
// requests/events/test_event.json
{
    "type": "content_analysis",
    "data": {
        "content": "Test content...",
        "options": {
            "analyze_sentiment": true,
            "extract_keywords": true
        }
    }
}
```

2. **Local Workflow Testing**:

```python
# test_workflow.py
from playground.utils import EventFactory


def test_workflow():
    # Load test event
    event = EventFactory.create_event("test_event")

    # Run workflow
    workflow = YourWorkflow()
    result = workflow.run(event)

    # Validate results
    print(result.nodes)
```

3. **API Integration Testing**:
```bash
# Test through API
python requests/send_event.py test_event.json
```

## Best Practices

### 1. Event Organization

Structure your test events logically:
```
requests/events/
├── support/
│   ├── basic_inquiry.json
│   └── urgent_issue.json
├── content/
│   ├── article_analysis.json
│   └── translation.json
└── validation/
    ├── edge_cases.json
    └── error_scenarios.json
```

### 2. Event Validation

Include validation in your test events:
```python
def validate_event(event: EventSchema):
    """Validate event structure and data."""
    assert event.type in VALID_EVENT_TYPES
    assert all(required in event.data for required in REQUIRED_FIELDS)
```

### 3. Test Coverage

Create events for different scenarios:
```python
# Test different event types
for event_key in EventFactory.get_all_event_keys():
    event = EventFactory.create_event(event_key)
    result = workflow.run(event)
    validate_result(result)
```

### 4. Development Tips

1. **Local Development**:
```python
# Quick workflow testing
event = EventFactory.create_event("your_test_event")
workflow = YourWorkflow()
result = workflow.run(event)
```

2. **Result Validation**:
```python
# Validate workflow results
def validate_workflow_result(result):
    assert "AnalyzeNode" in result.nodes
    assert isinstance(result.nodes["AnalyzeNode"], dict)
    assert "confidence" in result.nodes["AnalyzeNode"]
```

The event testing system provides a flexible and robust way to develop and test your AI workflows, whether you're working locally or testing the complete system through the API.