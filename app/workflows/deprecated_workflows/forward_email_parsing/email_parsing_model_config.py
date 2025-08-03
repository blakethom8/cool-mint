"""
Email Parsing Workflow Model Configuration

This module provides model configuration specific to the email parsing workflow.
It allows independent model selection without affecting other workflows.
"""

import os
from typing import Tuple
from dotenv import load_dotenv

from core.nodes.agent import ModelProvider

load_dotenv()


class EmailParsingModelConfig:
    """Model configuration specific to email parsing workflow"""
    
    # Workflow-specific environment variables
    PROVIDER_ENV = "EMAIL_PARSING_MODEL_PROVIDER"
    DEFAULT_MODEL_ENV = "EMAIL_PARSING_DEFAULT_MODEL"
    FAST_MODEL_ENV = "EMAIL_PARSING_FAST_MODEL"
    
    # Default provider for this workflow
    DEFAULT_PROVIDER = os.getenv(PROVIDER_ENV, ModelProvider.ANTHROPIC.value)
    
    # Default models for each provider
    DEFAULT_MODELS = {
        ModelProvider.OPENAI: os.getenv(DEFAULT_MODEL_ENV, "gpt-4"),
        ModelProvider.ANTHROPIC: os.getenv(DEFAULT_MODEL_ENV, "claude-3-5-sonnet-20241022"),
        ModelProvider.GEMINI: os.getenv(DEFAULT_MODEL_ENV, "gemini-pro"),
        ModelProvider.BEDROCK: os.getenv(DEFAULT_MODEL_ENV, "anthropic.claude-v2"),
        ModelProvider.OLLAMA: os.getenv(DEFAULT_MODEL_ENV, "llama2"),
        ModelProvider.AZURE_OPENAI: os.getenv(DEFAULT_MODEL_ENV, "gpt-4")
    }
    
    # Fast models for simple tasks (classification, routing)
    FAST_MODELS = {
        ModelProvider.OPENAI: os.getenv(FAST_MODEL_ENV, "gpt-3.5-turbo"),
        ModelProvider.ANTHROPIC: os.getenv(FAST_MODEL_ENV, "claude-3-5-haiku-20241022"),
        ModelProvider.GEMINI: os.getenv(FAST_MODEL_ENV, "gemini-flash"),
        ModelProvider.BEDROCK: os.getenv(FAST_MODEL_ENV, "anthropic.claude-instant-v1"),
        ModelProvider.OLLAMA: os.getenv(FAST_MODEL_ENV, "mistral"),
        ModelProvider.AZURE_OPENAI: os.getenv(FAST_MODEL_ENV, "gpt-3.5-turbo")
    }
    
    @classmethod
    def get_provider(cls) -> ModelProvider:
        """Get the model provider for email parsing workflow"""
        try:
            return ModelProvider(cls.DEFAULT_PROVIDER)
        except ValueError:
            print(f"Warning: Invalid provider '{cls.DEFAULT_PROVIDER}', falling back to Anthropic")
            return ModelProvider.ANTHROPIC
    
    @classmethod
    def get_model(cls, task_type: str = "default") -> Tuple[ModelProvider, str]:
        """
        Get model for specific task type in email parsing
        
        Args:
            task_type: Type of task - 'classification', 'extraction', 'default'
            
        Returns:
            Tuple of (provider, model_name)
        """
        provider = cls.get_provider()
        
        # Use fast model for classification/routing tasks
        if task_type in ['classification', 'routing']:
            model = cls.FAST_MODELS.get(provider, cls.FAST_MODELS[ModelProvider.ANTHROPIC])
        else:
            # Use default model for extraction and other tasks
            model = cls.DEFAULT_MODELS.get(provider, cls.DEFAULT_MODELS[ModelProvider.ANTHROPIC])
        
        return provider, model
    
    @classmethod
    def get_config_summary(cls) -> dict:
        """Get current configuration summary"""
        provider = cls.get_provider()
        return {
            "provider": provider.value,
            "default_model": cls.DEFAULT_MODELS.get(provider),
            "fast_model": cls.FAST_MODELS.get(provider),
            "env_vars": {
                "provider": f"{cls.PROVIDER_ENV}={os.getenv(cls.PROVIDER_ENV, 'not set')}",
                "default_model": f"{cls.DEFAULT_MODEL_ENV}={os.getenv(cls.DEFAULT_MODEL_ENV, 'not set')}",
                "fast_model": f"{cls.FAST_MODEL_ENV}={os.getenv(cls.FAST_MODEL_ENV, 'not set')}"
            }
        }
    
    @classmethod
    def validate_configuration(cls) -> bool:
        """Validate that the configuration is properly set up"""
        provider = cls.get_provider()
        
        # Check if API key is set for the provider
        api_key_mapping = {
            ModelProvider.OPENAI: "OPENAI_API_KEY",
            ModelProvider.ANTHROPIC: "ANTHROPIC_API_KEY",
            ModelProvider.GEMINI: "GEMINI_API_KEY",
            ModelProvider.BEDROCK: "BEDROCK_AWS_ACCESS_KEY_ID",
            ModelProvider.OLLAMA: "OLLAMA_BASE_URL",
            ModelProvider.AZURE_OPENAI: "AZURE_OPENAI_API_KEY"
        }
        
        required_key = api_key_mapping.get(provider)
        if required_key and not os.getenv(required_key):
            print(f"Warning: {required_key} not set for provider {provider.value}")
            return False
        
        return True