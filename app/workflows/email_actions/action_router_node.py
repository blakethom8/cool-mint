from core.nodes.base import Node
from core.nodes.router import BaseRouter
from core.task import TaskContext


class ActionRouterNode(BaseRouter):
    """Routes to appropriate extraction node based on classified action type"""
    
    def process(self, task_context: TaskContext) -> TaskContext:
        """Process routing decision"""
        # Just pass through - routing happens in route() method
        return task_context
    
    def route(self, task_context: TaskContext):
        """Determine which node to route to based on action classification"""
        # Import nodes here to avoid circular imports
        from workflows.email_actions.add_note_extraction_node import AddNoteExtractionNode
        from workflows.email_actions.log_call_extraction_node import LogCallExtractionNode
        from workflows.email_actions.set_reminder_extraction_node import SetReminderExtractionNode
        from workflows.email_actions.unknown_action_node import UnknownActionNode
        
        # Get the classification results
        classification_data = task_context.nodes.get("IntentClassificationNode", {})
        action_type = classification_data.get("action_type", "unknown")
        
        # Map action types to node instances
        if action_type == "add_note":
            return AddNoteExtractionNode()
        elif action_type == "log_call":
            return LogCallExtractionNode()
        elif action_type == "set_reminder":
            return SetReminderExtractionNode()
        else:
            return UnknownActionNode()