from abc import ABC, abstractmethod
from typing import Any, Dict, List, Type, Tuple

import instructor
from anthropic import Anthropic
from config.settings import get_settings
from openai import OpenAI
from pydantic import BaseModel

"""
LLM Factory and Provider System

This module implements a flexible system for integrating various Language Model (LLM) providers
using a factory pattern. It supports multiple providers and can be easily extended.

For detailed documentation, including how to implement new providers and use the system,
please refer to the full documentation at:

docs/llm_factory.md

Brief overview:
- Uses a factory pattern to create LLM providers (OpenAI, Anthropic, Llama, etc.)
- Supports structured output using Pydantic models via the Instructor library
- Easily extensible for new LLM providers
"""


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def _initialize_client(self) -> Any:
        """Initialize the client for the LLM provider."""
        pass

    @abstractmethod
    def create_completion(
        self, response_model: Type[BaseModel], messages: List[Dict[str, str]], **kwargs
    ) -> Any:
        """Create a completion using the LLM provider."""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI provider implementation."""

    def __init__(self, settings):
        self.settings = settings
        self.client = self._initialize_client()

    def _initialize_client(self) -> Any:
        return instructor.from_openai(OpenAI(api_key=self.settings.api_key))

    def create_completion(
        self, response_model: Type[BaseModel], messages: List[Dict[str, str]], **kwargs
    ) -> Tuple[BaseModel, Any]:
        completion_params = {
            "model": kwargs.get("model", self.settings.default_model),
            "temperature": kwargs.get("temperature", self.settings.temperature),
            "max_retries": kwargs.get("max_retries", self.settings.max_retries),
            "max_tokens": kwargs.get("max_tokens", self.settings.max_tokens),
            "response_model": response_model,
            "messages": messages,
        }
        return self.client.chat.completions.create_with_completion(**completion_params)


class AnthropicProvider(LLMProvider):
    """Anthropic provider implementation."""

    def __init__(self, settings):
        self.settings = settings
        self.client = self._initialize_client()

    def _initialize_client(self) -> Any:
        return instructor.from_anthropic(Anthropic(api_key=self.settings.api_key))

    def create_completion(
        self, response_model: Type[BaseModel], messages: List[Dict[str, str]], **kwargs
    ) -> Any:
        system_message = next(
            (m["content"] for m in messages if m["role"] == "system"), None
        )
        user_messages = [m for m in messages if m["role"] != "system"]

        completion_params = {
            "model": kwargs.get("model", self.settings.default_model),
            "temperature": kwargs.get("temperature", self.settings.temperature),
            "max_retries": kwargs.get("max_retries", self.settings.max_retries),
            "max_tokens": kwargs.get("max_tokens", self.settings.max_tokens),
            "response_model": response_model,
            "messages": user_messages,
        }
        if system_message:
            completion_params["system"] = system_message

        return self.client.messages.create_with_completion(**completion_params)


class LlamaProvider(LLMProvider):
    """Llama provider implementation."""

    def __init__(self, settings):
        self.settings = settings
        self.client = self._initialize_client()

    def _initialize_client(self) -> Any:
        return instructor.from_openai(
            OpenAI(base_url=self.settings.base_url, api_key=self.settings.api_key),
            mode=instructor.Mode.JSON,
        )

    def create_completion(
        self, response_model: Type[BaseModel], messages: List[Dict[str, str]], **kwargs
    ) -> Any:
        completion_params = {
            "model": kwargs.get("model", self.settings.default_model),
            "temperature": kwargs.get("temperature", self.settings.temperature),
            "max_retries": kwargs.get("max_retries", self.settings.max_retries),
            "max_tokens": kwargs.get("max_tokens", self.settings.max_tokens),
            "response_model": response_model,
            "messages": messages,
        }
        return self.client.chat.completions.create_with_completion(**completion_params)


class LLMFactory:
    """Factory class for creating LLM providers."""

    def __init__(self, provider: str):
        self.provider = provider
        settings = get_settings()
        self.settings = getattr(settings.llm, provider)
        self.llm_provider = self._create_provider()

    def _create_provider(self) -> LLMProvider:
        providers = {
            "openai": OpenAIProvider,
            "anthropic": AnthropicProvider,
            "llama": LlamaProvider,
        }
        provider_class = providers.get(self.provider)
        if provider_class:
            return provider_class(self.settings)
        raise ValueError(f"Unsupported LLM provider: {self.provider}")

    def create_completion(
        self, response_model: Type[BaseModel], messages: List[Dict[str, str]], **kwargs
    ) -> Tuple[BaseModel, Any]:
        if not issubclass(response_model, BaseModel):
            raise TypeError("response_model must be a subclass of pydantic.BaseModel")

        return self.llm_provider.create_completion(response_model, messages, **kwargs)
