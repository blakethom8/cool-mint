from core.nodes.base import Node
from core.task import TaskContext


class UnknownActionNode(Node):
    """Handles cases where the action type couldn't be determined"""
    
    def process(self, task_context: TaskContext) -> TaskContext:
        """Mark the email as having an unknown action type"""
        
        # Get classification data
        classification = task_context.nodes.get("IntentClassificationNode", {})
        
        task_context.update_node(
            node_name=self.node_name,
            status="unknown_action",
            message="Could not determine a specific action for this email",
            classification_reasoning=classification.get("reasoning", "No classification available")
        )
        
        return task_context