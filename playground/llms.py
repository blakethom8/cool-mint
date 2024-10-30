import sys

sys.path.append("..")

from services.llm_factory import LLMFactory
from pipelines.customer.analyze_ticket import CustomerIntent
from pydantic import BaseModel

llm = LLMFactory(provider="openai")

# --------------------------------------------------------------
# Test your LLM with structured output
# --------------------------------------------------------------


class IntentModel(BaseModel):
    intent: CustomerIntent


intent, completion = llm.create_completion(
    response_model=IntentModel,
    messages=[
        {
            "role": "user",
            "content": "Can I have my invoice for order #123456?",
        },
    ],
)

print(intent)
