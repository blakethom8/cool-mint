import sys
from enum import Enum
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / "app"))

from services.llm_factory import LLMFactory  # noqa: E402
from pydantic import BaseModel  # noqa: E402

"""
This playground is used to test the LLMFactory and the LLM classes.
"""

llm = LLMFactory(provider="openai")


# --------------------------------------------------------------
# Test your LLM with structured output
# --------------------------------------------------------------


class CustomerIntent(str, Enum):
    GENERAL_QUESTION = "general/question"
    PRODUCT_QUESTION = "product/question"
    BILLING_INVOICE = "billing/invoice"
    REFUND_REQUEST = "refund/request"

    @property
    def escalate(self) -> bool:
        return self in {
            self.REFUND_REQUEST,
        }


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
