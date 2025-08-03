"""Email actions workflow nodes package"""

# Import shared nodes
from .intent_classification_node import IntentClassificationNode
from .action_router_node import ActionRouterNode
from .create_staging_record_node import CreateStagingRecordNode
from .unknown_action_node import UnknownActionNode

# Import action-specific nodes
from .log_call.log_call_extraction_node import LogCallExtractionNode
from .set_reminder.set_reminder_extraction_node import SetReminderExtractionNode
from .add_note.add_note_extraction_node import AddNoteExtractionNode

__all__ = [
    'IntentClassificationNode',
    'ActionRouterNode',
    'CreateStagingRecordNode',
    'UnknownActionNode',
    'LogCallExtractionNode',
    'SetReminderExtractionNode',
    'AddNoteExtractionNode',
]