"""
Target Identification Node

This node analyzes healthcare provider data to identify high-potential targets
for referral network development.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from app.core.nodes.agent import AgentNode, AgentConfig, ModelProvider
from app.core.task import TaskContext
from app.services.prompt_loader import PromptManager


class TargetProvider(BaseModel):
    """Individual provider target information."""

    name: str = Field(description="Provider's full name")
    organization: str = Field(description="Provider's primary organization")
    practice_location: str = Field(description="Provider's practice location")
    visit_volume: int = Field(description="Provider's total visit volume")
    rationale: List[str] = Field(
        description="Specific reasons why this provider would be a good referral target",
        default_factory=list,
    )
    opportunity_score: float = Field(
        description="Score indicating the strength of the referral opportunity (0-1)",
        ge=0,
        le=1,
        default=0.5,
    )


class TargetIdentifyNode(AgentNode):
    """Analyzes market data to identify potential referral targets."""

    class OutputType(BaseModel):
        """Output schema for target identification."""

        priority_targets: List[TargetProvider] = Field(
            description="High-priority providers to target for referral network development",
            max_items=5,
            default_factory=list,
        )
        market_insights: List[str] = Field(
            description="Key insights about the market and referral opportunities",
            default_factory=list,
        )
        network_gaps: List[str] = Field(
            description="Identified gaps in current referral network coverage",
            default_factory=list,
        )
        approach_recommendations: Dict[str, List[str]] = Field(
            description="Recommended approach strategies for each target provider",
            default_factory=dict,
        )
        overall_confidence: float = Field(
            description="Overall confidence in the target recommendations (0-1)",
            ge=0,
            le=1,
            default=0.5,
        )

    def __init__(self):
        self.prompt_loader = PromptManager()
        # Load the prompt data before initializing parent
        self.prompt_data = self.prompt_loader.get_prompt(
            "market_exploration/target_identification"
        )
        super().__init__()

    def get_agent_config(self) -> AgentConfig:
        return AgentConfig(
            system_prompt=self.prompt_data.system_prompt,
            output_type=self.OutputType,
            deps_type=None,
            model_provider=ModelProvider(self.prompt_data.model.provider),
            model_name=self.prompt_data.model.name,
            instrument=True,
        )

    def process(self, task_context: TaskContext) -> TaskContext:
        """Process the market data and identify referral targets."""
        market_data = task_context.event.market_data

        # Capture prompts for tracing
        self._capture_prompts(task_context, market_data)

        result = self.agent.run_sync(user_prompt=market_data)

        # Store the identification result
        task_context.update_node(node_name=self.node_name, result=result.data)
        task_context.metadata["target_identification"] = result.data

        # Store the completion if available
        if hasattr(result, "completion"):
            task_context.metadata["completion"] = result.completion

        return task_context
