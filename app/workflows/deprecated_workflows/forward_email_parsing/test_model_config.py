#!/usr/bin/env python3
"""
Test model configuration and switching
"""

import os
import sys

# Add the app directory to Python path
app_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, app_dir)

from core.model_config import ModelConfig
from core.nodes.agent import ModelProvider


def test_model_config():
    """Test the model configuration system"""
    
    print("Model Configuration Test")
    print("=" * 80)
    
    # Test default provider
    default_provider = ModelConfig.get_default_provider()
    print(f"Default Provider: {default_provider.value}")
    
    # Test default models
    print("\nDefault Models:")
    for provider in ModelProvider:
        model = ModelConfig.get_default_model(provider)
        print(f"  {provider.value}: {model}")
    
    # Test fast models
    print("\nFast Models:")
    for provider in ModelProvider:
        model = ModelConfig.get_default_model(provider, fast=True)
        print(f"  {provider.value}: {model}")
    
    # Test task-specific models
    print("\nTask-Specific Models:")
    tasks = ['classification', 'extraction', 'generation']
    for task in tasks:
        provider, model = ModelConfig.get_model_for_task(task)
        print(f"  {task}: {provider.value} - {model}")
    
    # Show how to switch providers
    print("\n" + "=" * 80)
    print("To switch providers, set DEFAULT_MODEL_PROVIDER in .env:")
    print("  DEFAULT_MODEL_PROVIDER=openai")
    print("  DEFAULT_MODEL_PROVIDER=anthropic")
    print("  DEFAULT_MODEL_PROVIDER=gemini")
    print("\nOr set it temporarily:")
    print("  export DEFAULT_MODEL_PROVIDER=anthropic")
    
    # Check API keys
    print("\n" + "=" * 80)
    print("API Key Status:")
    api_keys = {
        "OPENAI_API_KEY": "OpenAI",
        "ANTHROPIC_API_KEY": "Anthropic",
        "GEMINI_API_KEY": "Gemini",
        "BEDROCK_AWS_ACCESS_KEY_ID": "AWS Bedrock"
    }
    
    for key, provider in api_keys.items():
        value = os.getenv(key)
        if value:
            masked = value[:10] + "..." if len(value) > 10 else "***"
            print(f"  {provider}: ✓ Set ({masked})")
        else:
            print(f"  {provider}: ✗ Not set")


if __name__ == "__main__":
    test_model_config()