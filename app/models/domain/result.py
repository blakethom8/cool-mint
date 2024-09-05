from pydantic import BaseModel, Field


class TaskResult(BaseModel):
    reasoning: str = Field(description="The reasoning for the response")
    response: str = Field(description="The response to the ticket")
    confidence: float = Field(
        ge=0, le=1, description="Confidence score for how helpful the response is"
    )
