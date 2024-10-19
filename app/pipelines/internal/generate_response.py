from core.llm import LLMStep
from services.prompt_loader import PromptManager
from pydantic import BaseModel, Field
from core.task import TaskContext
from services.llm_factory import LLMFactory
from services.vector_store import VectorStore


class GenerateResponse(LLMStep):
    """
    A step to generate a response for an internal ticket.

    This class inherits from LLMStep and implements the necessary methods
    to process an internal ticket and generate a response using RAG.

    Attributes:
        vector_store (VectorStore): An instance of VectorStore for semantic search.
    """

    class ContextModel(BaseModel):
        sender: str
        subject: str
        body: str

    class ResponseModel(BaseModel):
        reasoning: str = Field(description="The reasoning for the response")
        response: str = Field(description="The response to the ticket")

    def __init__(self):
        super().__init__()
        self.vector_store = VectorStore()

    def get_context(self, task_context: TaskContext) -> ContextModel:
        return self.ContextModel(
            sender=task_context.event.sender,
            subject=task_context.event.subject,
            body=task_context.event.body,
        )

    def search_kb(self, query: str) -> list[str]:
        results = self.vector_store.semantic_search(
            query=query,
            limit=5,
            metadata_filter={"category": "internal"},
            return_dataframe=True,
        )
        return results["contents"].tolist()

    def create_completion(
        self, context: ContextModel
    ) -> tuple[ResponseModel, list[str]]:
        rag_context = self.search_kb(context.body)
        llm = LLMFactory("openai")
        SYSTEM_PROMPT = PromptManager.get_prompt(template="internal_ticket_response")
        completion = llm.create_completion(
            response_model=self.ResponseModel,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": f"# New ticket:\n{context.model_dump()}",
                },
                {
                    "role": "assistant",
                    "content": f"# Retrieved information:\n{rag_context}",
                },
            ],
        )
        return completion, rag_context

    def process(self, task_context: TaskContext) -> TaskContext:
        context: self.ContextModel = self.get_context(task_context)
        completion, rag_context = self.create_completion(context)
        task_context.steps[self.step_name] = {
            "completion": completion,
            "rag_context": rag_context,
        }
        return task_context
