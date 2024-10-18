import logging

from models.domain.intent import InternalIntent
from models.domain.task import TaskContext
from pipelines.base import PipelineStep
from prompts.prompt_manager import PromptManager
from pydantic import BaseModel, Field
from services.llm_factory import LLMFactory
from utils.event_factory import EventFactory


class AnalysisResponseModel(BaseModel):
    reasoning: str = Field(
        description="Explain your reasoning for the intent classification"
    )
    intent: InternalIntent
    confidence: float = Field(ge=0, le=1, description="Confidence score for the intent")


class TicketAnalysisData(BaseModel):
    sender: str
    subject: str
    body: str


class ContextExtractor:
    @staticmethod
    def get_context(task_context: TaskContext) -> TicketAnalysisData:
        return TicketAnalysisData(
            subject=task_context.event.subject,
            body=task_context.event.body,
            sender=task_context.event.sender,
        )


class TicketAnalysis(PipelineStep):
    def process(self, task_context: TaskContext) -> TaskContext:
        logging.info(f"Running {self.step_name}")
        llm_context = ContextExtractor.get_context(task_context)
        completion = self.analyze_input(llm_context)
        task_context.steps[self.step_name] = completion
        return task_context

    def analyze_input(self, llm_context: TicketAnalysisData) -> AnalysisResponseModel:
        llm = LLMFactory("openai")
        prompt = PromptManager.get_prompt(
            "ticket_analysis",
            pipeline="helpdesk",
            ticket=llm_context,
        )
        completion = llm.create_completion(
            response_model=AnalysisResponseModel,
            messages=[
                {
                    "role": "system",
                    "content": prompt,
                },
            ],
        )
        return completion


if __name__ == "__main__":
    ticket_analysis = TicketAnalysis()
    event = EventFactory.create_event(event_key="invoice")
    task_context = TaskContext(event=event)
    result = ticket_analysis.process(task_context)
