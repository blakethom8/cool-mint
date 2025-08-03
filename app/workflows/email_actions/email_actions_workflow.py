from core.workflow import Workflow, WorkflowSchema, NodeConfig
from schemas.email_actions_schema import EmailActionsEventSchema

# Import all nodes from the new structure
from workflows.email_actions.email_actions_nodes import (
    IntentClassificationNode,
    ActionRouterNode,
    LogCallExtractionNode,
    AddNoteExtractionNode,
    SetReminderExtractionNode,
    UnknownActionNode,
    EntityMatchingNode,
    CreateStagingRecordNode
)


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
                connections=[EntityMatchingNode],
                description="Extract call/meeting log parameters"
            ),
            NodeConfig(
                node=AddNoteExtractionNode,
                connections=[EntityMatchingNode],
                description="Extract note parameters"
            ),
            NodeConfig(
                node=SetReminderExtractionNode,
                connections=[EntityMatchingNode],  # Now route through entity matching
                description="Extract reminder parameters"
            ),
            NodeConfig(
                node=EntityMatchingNode,
                connections=[CreateStagingRecordNode],
                description="Match extracted entities to database records"
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