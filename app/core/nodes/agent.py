"""
Agent Node Implementation

This module provides the AgentNode class which integrates with LLM providers
to process tasks using conversational AI agents.
"""

import boto3
import os
import json
from abc import abstractmethod, ABC
from dataclasses import dataclass
from dotenv import load_dotenv
from enum import Enum
from httpx import AsyncClient
from openai import AsyncAzureOpenAI, OpenAI
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models import Model
from pydantic_ai.models.anthropic import AnthropicModel, AnthropicModelName
from pydantic_ai.models.bedrock import BedrockConverseModel, BedrockModelName
from pydantic_ai.models.gemini import GeminiModel, GeminiModelName
from pydantic_ai.models.openai import OpenAIModel, OpenAIModelName
from pydantic_ai.providers.anthropic import AnthropicProvider
from pydantic_ai.providers.bedrock import BedrockProvider
from pydantic_ai.providers.google_gla import GoogleGLAProvider
from pydantic_ai.providers.openai import OpenAIProvider
from typing import Type, Optional, Union, Any, Dict, List
from langfuse import Langfuse
from langfuse.decorators import observe

from app.core.nodes.base import Node
from app.core.task import TaskContext

load_dotenv()


class ModelProvider(str, Enum):
    OPENAI = "openai"
    AZURE_OPENAI = "azure_openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    OLLAMA = "ollama"
    BEDROCK = "bedrock"


@dataclass
class AgentConfig:
    """
    Represents the configuration settings for an Agent.

    Attributes:
        system_prompt (str): The system prompt to initialize the agent with.
        output_type (Optional[Type[Any]]): The output type of the agent's responses.
        deps_type (Optional[Type[Any]]): The type used for managing dependencies.
        model_provider (ModelProvider): The provider that supplies the model for the agent.
        model_name (Union[OpenAIModelName, AnthropicModelName, GeminiModelName,
            BedrockModelName]): The name of the specific model to be used.
        instrument (bool): Indicates whether instrumentation is enabled for
            the agent. This should be set to True for Langfuse traces. Defaults to False.
    """

    system_prompt: str
    output_type: Optional[Type[Any]]
    deps_type: Optional[Type[Any]]
    model_provider: ModelProvider
    model_name: Union[
        OpenAIModelName, AnthropicModelName, GeminiModelName, BedrockModelName
    ]
    instrument: bool = False


class AgentNode(Node, ABC):
    class DepsType(BaseModel):
        pass

    class OutputType(BaseModel):
        pass

    def __init__(self):
        self.__async_client = AsyncClient()
        self.agent_config = self.get_agent_config()
        self.agent = Agent(
            system_prompt=self.agent_config.system_prompt,
            output_type=self.agent_config.output_type,
            model=self.__get_model_instance(
                self.agent_config.model_provider, self.agent_config.model_name
            ),
            instrument=self.agent_config.instrument,
        )

    def _capture_prompts(self, task_context: TaskContext, user_prompt: str):
        """Capture prompts and model info in the task context for tracing."""
        task_context.metadata["llm_details"] = {
            "system_prompt": self.agent_config.system_prompt,
            "user_prompt": user_prompt,
            "model": {
                "provider": self.agent_config.model_provider.value,
                "name": self.agent_config.model_name,
            },
        }

    @abstractmethod
    def get_agent_config(self) -> AgentConfig:
        pass

    @abstractmethod
    def process(self, task_context: TaskContext) -> TaskContext:
        pass

    def __get_model_instance(self, provider: ModelProvider, model_name: str) -> Model:
        match provider.value:
            case provider.OPENAI.value:
                return self.__get_openai_model(model_name)
            case provider.AZURE_OPENAI.value:
                return self.__get_azure_openai_model(model_name)
            case provider.ANTHROPIC.value:
                return self.__get_anthropic_model(model_name)
            case provider.GEMINI.value:
                return self.__get_gemini_model(model_name)
            case provider.OLLAMA.value:
                return self.__get_ollama_model(model_name)
            case provider.BEDROCK.value:
                return self.__get_bedrock_model(model_name)
            case _:
                return self.__get_openai_model("gpt-4.1")

    def __get_openai_model(self, model_name: OpenAIModelName) -> Model:
        return OpenAIModel(
            model_name,
            provider=OpenAIProvider(http_client=self.__async_client),
        )

    def __get_azure_openai_model(self, model_name: OpenAIModelName) -> Model:
        client = AsyncAzureOpenAI()
        return OpenAIModel(
            model_name,
            provider=OpenAIProvider(openai_client=client),
        )

    def __get_anthropic_model(self, model_name: AnthropicModelName) -> Model:
        return AnthropicModel(
            model_name=model_name,
            provider=AnthropicProvider(http_client=self.__async_client),
        )

    def __get_gemini_model(self, model_name: str) -> Model:
        return GeminiModel(
            model_name=model_name,
            provider=GoogleGLAProvider(http_client=self.__async_client),
        )

    def __get_ollama_model(self, model_name: str) -> Model:
        base_url = os.getenv("OLLAMA_BASE_URL")
        if not base_url:
            raise KeyError("OLLAMA_BASE_URL not set in .env")

        return OpenAIModel(
            model_name=model_name, provider=OpenAIProvider(base_url=base_url)
        )

    def __get_bedrock_model(self, model_name: str) -> Model:
        aws_access_key_id = os.getenv("BEDROCK_AWS_ACCESS_KEY_ID")
        aws_secret_access_key = os.getenv("BEDROCK_AWS_SECRET_ACCESS_KEY")
        aws_region = os.getenv("BEDROCK_AWS_REGION")

        bedrock_client = boto3.client(
            "bedrock-runtime",
            region_name=aws_region,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
        )
        return BedrockConverseModel(
            model_name=model_name,
            provider=BedrockProvider(bedrock_client=bedrock_client),
        )
