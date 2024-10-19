from enum import Enum
from pipelines.core.task import TaskContext
from pipelines.core.llm import LLMStep
from services.prompt import PromptManager
from pydantic import BaseModel, Field
from services.llm import LLMFactory


class InternalIntent(str, Enum):
    IT_SUPPORT = "it/support"
    SOFTWARE_REQUEST = "software/request"
    POLICY_QUESTION = "policy/question"
    ACCESS_MANAGEMENT = "access/management"
    HARDWARE_ISSUE = "hardware/issue"

    @property
    def escalate(self) -> bool:
        return self in {
            self.ACCESS_MANAGEMENT,
        }


class AnalyzeTicket(LLMStep):
    class ContextModel(BaseModel):
        sender: str
        subject: str
        body: str

    class ResponseModel(BaseModel):
        reasoning: str = Field(
            description="Explain your reasoning for the intent classification"
        )
        intent: InternalIntent
        confidence: float = Field(
            ge=0, le=1, description="Confidence score for the intent"
        )

    def get_context(self, task_context: TaskContext) -> ContextModel:
        return self.ContextModel(
            sender=task_context.event.sender,
            subject=task_context.event.subject,
            body=task_context.event.body,
        )

    def create_completion(self, context: ContextModel) -> ResponseModel:
        llm = LLMFactory("openai")
        prompt = PromptManager.get_prompt(
            "ticket_analysis",
            pipeline="helpdesk",
        )
        return llm.create_completion(
            response_model=self.ResponseModel,
            messages=[
                {
                    "role": "system",
                    "content": prompt,
                },
                {
                    "role": "user",
                    "content": f"# New ticket:\n{context.model_dump()}",
                },
            ],
        )

    def process(self, task_context: TaskContext) -> TaskContext:
        context: self.ContextModel = self.get_context(task_context)
        completion: self.ResponseModel = self.create_completion(context)
        task_context.steps[self.step_name] = completion
        return task_context
