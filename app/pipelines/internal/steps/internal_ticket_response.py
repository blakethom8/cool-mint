from pipelines.base import PipelineStep
from prompts.prompt_manager import PromptManager
from pydantic import BaseModel, Field
from models.domain.task import TaskContext
from services.llm_factory import LLMFactory
from services.rag_service import RAGService
from models.domain.task import TaskResult


class ReponseModel(BaseModel):
    reasoning: str = Field(description="The reasoning for the response")
    response: str = Field(description="The response to the ticket")


class ReponseData(BaseModel):
    sender: str
    subject: str
    body: str


class ContextExtractor:
    @staticmethod
    def get_context(task_context: TaskContext) -> ReponseData:
        return ReponseData(
            sender=task_context.event.sender,
            subject=task_context.event.subject,
            body=task_context.event.body,
        )


class TicketResponse(PipelineStep):
    def process(self, task_context: TaskContext):
        llm_context = ContextExtractor.get_context(task_context)
        rag_context = self.search_kb(llm_context.body)
        completion = self.generate_response(
            llm_context=llm_context,
            rag_context=rag_context,
        )
        task_context.steps[self.step_name] = {"rag_context": rag_context}
        task_context.result = completion
        return task_context

    def search_kb(self, query: str):
        rag_service = RAGService()
        return rag_service.search(query)

    def generate_response(
        self, llm_context: ReponseData, rag_context: list
    ) -> TaskResult:
        llm = LLMFactory("openai")
        prompt = PromptManager.get_prompt(
            template="internal_ticket_response",
            ticket=llm_context,
            rag_context=rag_context,
        )
        completion = llm.create_completion(
            response_model=TaskResult,
            messages=[
                {
                    "role": "system",
                    "content": prompt,
                },
            ],
        )
        return completion
