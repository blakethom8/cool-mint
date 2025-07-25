from core.nodes.agent import AgentNode
from core.task import TaskContext
from dotenv import load_dotenv
from enum import Enum
from pydantic import Field
from pydantic_ai import RunContext

from core.nodes.agent import AgentConfig, ModelProvider
from schemas.nylas_email_schema import EmailObject

load_dotenv()


class EmailCategory(str, Enum):
    SPAM = "spam"
    MESSAGE = "general"
    INVOICE = "invoice"
    OTHER = "other"
    GENAI_ACCELERATOR = "genai_accelerator"


PROMPT = """
You are an intelligent email classification assistant. Your role is to accurately categorize incoming emails to ensure they are routed to the appropriate handling system.

## Classification Categories

**GENERAL**: General business communications and inquiries
- Partnership or collaboration proposals
- Speaking engagement requests
- General questions about AI or Dave's work
- Media interview requests
- Personal messages from colleagues or contacts

**INVOICE**: Financial and billing related communications
- Payment confirmations or receipts
- Subscription renewals or cancellations
- Refund requests
- Billing inquiries or disputes
- Tax documents or financial statements

**SPAM**: Unwanted promotional or suspicious emails
- Unsolicited marketing emails
- Phishing attempts or suspicious links
- Automated promotional content
- Irrelevant mass mailings
- Obviously fraudulent messages

**OTHER**: Legitimate emails that don't fit the above categories
- Newsletter subscriptions or unsubscribes
- Platform notifications (GitHub, LinkedIn, etc.)
- Event invitations or announcements
- Technical notifications from services
- Administrative emails from platforms or services

**GENAI_ACCELERATOR**: Emails directly related to the GenAI Accelerator program
- Student questions about coursework, assignments, or projects
- Requests for office hours or mentorship
- Technical support for course materials or platforms
- Community discussions and collaboration requests
- Course feedback or suggestions
- Applications or inquiries about joining the program


Classify the following email:
"""


class ClassificationNode(AgentNode):
    class OutputType(AgentNode.OutputType):
        category: EmailCategory
        confidence: float = Field(
            ge=0, le=1, description="Confidence score for the category"
        )

    class DepsType(AgentNode.DepsType):
        from_email: str = Field(..., description="Email address of the sender")
        sender: str = Field(..., description="Name or identifier of the sender")
        subject: str = Field(..., description="Subject of the ticket")
        body: str = Field(..., description="The body of the ticket")

    def get_agent_config(self) -> AgentConfig:
        return AgentConfig(
            system_prompt=PROMPT,
            output_type=self.OutputType,
            deps_type=self.DepsType,
            model_provider=ModelProvider.OPENAI,
            model_name="gpt-4o-mini",
        )

    def process(self, task_context: TaskContext) -> TaskContext:
        email_object = EmailObject(**task_context.event.data["object"])
        deps = self.DepsType(
            from_email=email_object.from_[0].email,
            sender=email_object.from_[0].name,
            subject=email_object.subject,
            body=email_object.body,
        )

        @self.agent.system_prompt
        def add_ticket_context(
            ctx: RunContext[ClassificationNode.DepsType],
        ) -> str:
            return deps.model_dump_json(indent=2)

        result = self.agent.run_sync(
            user_prompt="Classify this email",
        )

        task_context.update_node(node_name=self.node_name, result=result)
        return task_context
