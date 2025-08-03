from core.schema import WorkflowSchema, NodeConfig
from core.workflow import Workflow
from schemas.email_parsing_schema import EmailParsingEventSchema
from workflows.deprecated_workflows.forward_email_parsing.email_type_detection_node import (
    EmailTypeDetectionNode,
)
from workflows.deprecated_workflows.forward_email_parsing.forwarded_email_extraction_node import (
    ForwardedEmailExtractionNode,
)
from workflows.deprecated_workflows.forward_email_parsing.direct_email_extraction_node import (
    DirectEmailExtractionNode,
)
from workflows.deprecated_workflows.forward_email_parsing.entity_extraction_node import (
    EntityExtractionNode,
)
from workflows.deprecated_workflows.forward_email_parsing.meeting_details_extraction_node import (
    MeetingDetailsExtractionNode,
)
from workflows.deprecated_workflows.forward_email_parsing.action_item_extraction_node import (
    ActionItemExtractionNode,
)
from workflows.deprecated_workflows.forward_email_parsing.entity_resolution_node import (
    EntityResolutionNode,
)
from workflows.deprecated_workflows.forward_email_parsing.save_parsed_email_node import (
    SaveParsedEmailNode,
)


class ForwardEmailParsingWorkflow(Workflow):
    """Workflow for parsing forwarded emails and extracting structured data"""

    workflow_schema = WorkflowSchema(
        description="Parse and extract structured data from emails, especially forwarded emails with AI requests",
        event_schema=EmailParsingEventSchema,
        start=EmailTypeDetectionNode,
        nodes=[
            NodeConfig(
                node=EmailTypeDetectionNode,
                connections=[ForwardedEmailExtractionNode, DirectEmailExtractionNode],
                is_router=True,
                description="Detect if email is forwarded with user request",
            ),
            NodeConfig(
                node=ForwardedEmailExtractionNode,
                connections=[EntityExtractionNode],
                description="Extract user request and forwarded content",
            ),
            NodeConfig(
                node=DirectEmailExtractionNode,
                connections=[EntityExtractionNode],
                description="Process direct (non-forwarded) emails",
            ),
            NodeConfig(
                node=EntityExtractionNode,
                connections=[MeetingDetailsExtractionNode],
                description="Extract people, organizations, dates, and locations",
            ),
            NodeConfig(
                node=MeetingDetailsExtractionNode,
                connections=[ActionItemExtractionNode],
                description="Extract meeting-specific information if applicable",
            ),
            NodeConfig(
                node=ActionItemExtractionNode,
                connections=[EntityResolutionNode],
                description="Extract action items and tasks",
            ),
            NodeConfig(
                node=EntityResolutionNode,
                connections=[SaveParsedEmailNode],
                description="Map extracted entities to existing CRM records",
            ),
            NodeConfig(
                node=SaveParsedEmailNode,
                connections=[],
                description="Save all parsed data to emails_parsed table",
            ),
        ],
    )
