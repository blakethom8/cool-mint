"""
Model Configuration Module

This module provides centralized configuration for AI model providers and models.
It allows easy switching between different providers through environment variables
or configuration settings.
"""

import os
from enum import Enum
from typing import Union
from dotenv import load_dotenv

from core.nodes.agent import ModelProvider

load_dotenv()


class ModelConfig:
    """Central configuration for AI models used across the application"""
    
    # Default model provider - can be overridden by environment variable
    DEFAULT_PROVIDER = os.getenv("DEFAULT_MODEL_PROVIDER", ModelProvider.ANTHROPIC.value)
    
    # Default models for each provider
    DEFAULT_MODELS = {
        ModelProvider.OPENAI: "gpt-4",
        ModelProvider.ANTHROPIC: "claude-3-5-sonnet-20241022",  # Latest Claude 3.5 Sonnet
        ModelProvider.GEMINI: "gemini-pro",
        ModelProvider.BEDROCK: "anthropic.claude-v2",
        ModelProvider.OLLAMA: "llama2",
        ModelProvider.AZURE_OPENAI: "gpt-4"
    }
    
    # Fast models for simple tasks (lower cost, faster response)
    FAST_MODELS = {
        ModelProvider.OPENAI: "gpt-3.5-turbo",
        ModelProvider.ANTHROPIC: "claude-3-5-haiku-20241022",  # Claude 3.5 Haiku for speed
        ModelProvider.GEMINI: "gemini-flash",
        ModelProvider.BEDROCK: "anthropic.claude-instant-v1",
        ModelProvider.OLLAMA: "mistral",
        ModelProvider.AZURE_OPENAI: "gpt-3.5-turbo"
    }
    
    @classmethod
    def get_default_provider(cls) -> ModelProvider:
        """Get the default model provider from environment or configuration"""
        try:
            return ModelProvider(cls.DEFAULT_PROVIDER)
        except ValueError:
            # Fallback to Anthropic if invalid provider specified
            return ModelProvider.ANTHROPIC
    
    @classmethod
    def get_default_model(cls, provider: ModelProvider = None, fast: bool = False) -> str:
        """
        Get the default model for a provider
        
        Args:
            provider: The model provider (uses default if not specified)
            fast: Whether to use the fast/cheap model variant
            
        Returns:
            The model name string
        """
        if provider is None:
            provider = cls.get_default_provider()
        
        model_dict = cls.FAST_MODELS if fast else cls.DEFAULT_MODELS
        return model_dict.get(provider, cls.DEFAULT_MODELS[ModelProvider.ANTHROPIC])
    
    @classmethod
    def get_model_for_task(cls, task_type: str) -> tuple[ModelProvider, str]:
        """
        Get recommended model for specific task types
        
        Args:
            task_type: Type of task (e.g., 'classification', 'extraction', 'generation')
            
        Returns:
            Tuple of (provider, model_name)
        """
        provider = cls.get_default_provider()
        
        # Task-specific model selection
        if task_type in ['classification', 'routing']:
            # Use faster models for simple classification
            return provider, cls.get_default_model(provider, fast=True)
        elif task_type in ['extraction', 'analysis']:
            # Use standard models for extraction
            return provider, cls.get_default_model(provider, fast=False)
        else:
            # Default to standard model
            return provider, cls.get_default_model(provider, fast=False)