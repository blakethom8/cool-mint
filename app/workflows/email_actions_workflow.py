from core.workflow import Workflow, WorkflowSchema, NodeConfig
from schemas.email_actions_schema import EmailActionsEventSchema

# Import all nodes
from workflows.email_actions.intent_classification_node import IntentClassificationNode
from workflows.email_actions.action_router_node import ActionRouterNode
from workflows.email_actions.log_call_extraction_node import LogCallExtractionNode
from workflows.email_actions.add_note_extraction_node import AddNoteExtractionNode
from workflows.email_actions.set_reminder_extraction_node import SetReminderExtractionNode
from workflows.email_actions.unknown_action_node import UnknownActionNode
from workflows.email_actions.create_staging_record_node import CreateStagingRecordNode


class EmailActionsWorkflow(Workflow):
    """Workflow for classifying emails and extracting action-specific data"""
    
    workflow_schema = WorkflowSchema(
        description="Classifies email intents and extracts action parameters",
        event_schema=EmailActionsEventSchema,
        start=IntentClassificationNode,
        nodes=[
            NodeConfig(
                node=IntentClassificationNode,
                connections=[ActionRouterNode],
                description="Classify email intent into action types"
            ),
            NodeConfig(
                node=ActionRouterNode,
                connections=[
                    LogCallExtractionNode,
                    AddNoteExtractionNode,
                    SetReminderExtractionNode,
                    UnknownActionNode
                ],
                is_router=True,
                description="Route to appropriate extraction node"
            ),
            NodeConfig(
                node=LogCallExtractionNode,
                connections=[CreateStagingRecordNode],
                description="Extract call/meeting log parameters"
            ),
            NodeConfig(
                node=AddNoteExtractionNode,
                connections=[CreateStagingRecordNode],
                description="Extract note parameters"
            ),
            NodeConfig(
                node=SetReminderExtractionNode,
                connections=[CreateStagingRecordNode],
                description="Extract reminder parameters"
            ),
            NodeConfig(
                node=UnknownActionNode,
                connections=[],  # Terminal node
                description="Handle unknown action types"
            ),
            NodeConfig(
                node=CreateStagingRecordNode,
                connections=[],  # Terminal node
                description="Create staging records in database"
            ),
        ]
    )