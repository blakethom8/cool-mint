"""
Search Classification Node

This node determines whether a user's query requires a search
to gather additional information.
"""

from typing import Dict, Any, Literal, Optional
from pydantic import BaseModel, Field

from app.core.nodes.agent import AgentNode, AgentConfig, ModelProvider
from app.core.task import TaskContext
from app.services.prompt_loader import PromptManager


class SearchClassifierNode(AgentNode):
    """Classifies whether a user's query requires a search."""

    class OutputType(BaseModel):
        """
        Output schema for search classification.
        This schema defines whether a search is needed and why.
        """

        needs_search: bool = Field(
            description="Whether the query requires a search to gather additional information"
        )

        reason: str = Field(
            description="Explanation of why a search is or isn't needed"
        )

        original_query: str = Field(description="The original user query")

    def __init__(self):
        self.prompt_loader = PromptManager()
        # Load the prompt data before initializing parent
        self.prompt_data = self.prompt_loader.get_prompt(
            "market_exploration/google_search_classification"
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
        """Process the user query and determine if search is needed."""
        user_query = task_context.event.query

        # Capture prompts for tracing
        self._capture_prompts(task_context, user_query)

        result = self.agent.run_sync(user_prompt=user_query)

        # Store the classification result
        task_context.update_node(node_name=self.node_name, result=result.data)
        task_context.metadata["search_classification"] = result.data

        # Store the completion if available
        if hasattr(result, "completion"):
            task_context.metadata["completion"] = result.completion

        return task_context
