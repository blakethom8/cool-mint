"""
Model configuration for Email Actions workflow
"""
import os
from typing import Tuple, Optional
from core.nodes.agent import ModelProvider


class EmailActionsModelConfig:
    """Centralized model configuration for Email Actions workflow"""
    
    # Environment variable names
    PROVIDER_ENV = "EMAIL_ACTIONS_MODEL_PROVIDER"
    DEFAULT_MODEL_ENV = "EMAIL_ACTIONS_DEFAULT_MODEL"
    FAST_MODEL_ENV = "EMAIL_ACTIONS_FAST_MODEL"
    
    # Default values
    DEFAULT_PROVIDER = ModelProvider.ANTHROPIC
    DEFAULT_MODELS = {
        ModelProvider.OPENAI: {
            "default": "gpt-4",
            "fast": "gpt-3.5-turbo"
        },
        ModelProvider.ANTHROPIC: {
            "default": "claude-3-5-sonnet-20241022",
            "fast": "claude-3-5-haiku-20241022"
        },
        ModelProvider.GEMINI: {
            "default": "gemini-pro",
            "fast": "gemini-flash"
        }
    }
    
    @classmethod
    def get_provider(cls) -> ModelProvider:
        """Get the configured model provider"""
        provider_str = os.getenv(cls.PROVIDER_ENV, cls.DEFAULT_PROVIDER.value)
        
        # Map string to ModelProvider enum
        for provider in ModelProvider:
            if provider.value == provider_str:
                return provider
        
        # Default if not found
        return cls.DEFAULT_PROVIDER
    
    @classmethod
    def get_model(cls, task_type: str = "default") -> Tuple[ModelProvider, str]:
        """
        Get model configuration for a specific task type
        
        Args:
            task_type: Type of task ('classification', 'extraction', 'default')
            
        Returns:
            Tuple of (ModelProvider, model_name)
        """
        provider = cls.get_provider()
        
        # Determine which model to use based on task
        if task_type == "classification":
            # Use fast model for classification
            model_env = cls.FAST_MODEL_ENV
            default_model = cls.DEFAULT_MODELS.get(provider, {}).get("fast", "claude-3-5-haiku-20241022")
        else:
            # Use default model for extraction and other tasks
            model_env = cls.DEFAULT_MODEL_ENV
            default_model = cls.DEFAULT_MODELS.get(provider, {}).get("default", "claude-3-5-sonnet-20241022")
        
        # Get model from environment or use default
        model_name = os.getenv(model_env, default_model)
        
        return provider, model_name
    
    @classmethod
    def get_api_key(cls, provider: Optional[ModelProvider] = None) -> Optional[str]:
        """Get API key for the provider"""
        if provider is None:
            provider = cls.get_provider()
        
        key_mapping = {
            ModelProvider.OPENAI: "OPENAI_API_KEY",
            ModelProvider.ANTHROPIC: "ANTHROPIC_API_KEY",
            ModelProvider.GEMINI: "GEMINI_API_KEY",
            ModelProvider.BEDROCK: "BEDROCK_AWS_ACCESS_KEY_ID",
        }
        
        return os.getenv(key_mapping.get(provider, ""))
    
    @classmethod
    def get_config_summary(cls) -> dict:
        """Get current configuration summary"""
        provider = cls.get_provider()
        _, default_model = cls.get_model("default")
        _, fast_model = cls.get_model("classification")
        
        return {
            "provider": provider.value,
            "default_model": default_model,
            "fast_model": fast_model,
            "env_vars": {
                "provider": f"{cls.PROVIDER_ENV}={os.getenv(cls.PROVIDER_ENV, 'not set')}",
                "default_model": f"{cls.DEFAULT_MODEL_ENV}={os.getenv(cls.DEFAULT_MODEL_ENV, 'not set')}",
                "fast_model": f"{cls.FAST_MODEL_ENV}={os.getenv(cls.FAST_MODEL_ENV, 'not set')}"
            }
        }