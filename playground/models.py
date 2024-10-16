import sys

sys.path.append("..")

from app.services.llm_factory import LLMFactory
from app.models.domain.intent import CustomerIntent

llm = LLMFactory(provider="anthropic")


completion = llm.create_completion(
    response_model=CustomerIntent,
    messages=[
        {
            "role": "user",
            "content": "Can I have my invoice for order #123456?",
        },
    ],
)

print(completion)
