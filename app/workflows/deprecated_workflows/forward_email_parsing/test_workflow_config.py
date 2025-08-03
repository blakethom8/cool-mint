#!/usr/bin/env python3
"""
Test email parsing workflow configuration
"""

import os
import sys

# Add the app directory to Python path
app_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, app_dir)

from workflows.forward_email_parsing.email_parsing_model_config import EmailParsingModelConfig
from core.nodes.agent import ModelProvider


def test_workflow_config():
    """Test the email parsing workflow configuration"""
    
    print("Email Parsing Workflow Configuration")
    print("=" * 80)
    
    # Get configuration summary
    config = EmailParsingModelConfig.get_config_summary()
    
    print("\nCurrent Configuration:")
    print(f"  Provider: {config['provider']}")
    print(f"  Default Model: {config['default_model']}")
    print(f"  Fast Model: {config['fast_model']}")
    
    print("\nEnvironment Variables:")
    for key, value in config['env_vars'].items():
        print(f"  {value}")
    
    # Validate configuration
    print("\nConfiguration Validation:")
    is_valid = EmailParsingModelConfig.validate_configuration()
    print(f"  Valid: {'✓' if is_valid else '✗'}")
    
    # Show task-specific models
    print("\nTask-Specific Models:")
    tasks = ['classification', 'extraction', 'default']
    for task in tasks:
        provider, model = EmailParsingModelConfig.get_model(task)
        print(f"  {task}: {provider.value} - {model}")
    
    # Show how to configure
    print("\n" + "=" * 80)
    print("To configure this workflow, add to .env:")
    print("  EMAIL_PARSING_MODEL_PROVIDER=anthropic")
    print("  EMAIL_PARSING_DEFAULT_MODEL=claude-3-5-sonnet-20241022")
    print("  EMAIL_PARSING_FAST_MODEL=claude-3-5-haiku-20241022")
    
    print("\nSupported providers:")
    for provider in ModelProvider:
        print(f"  - {provider.value}")
    
    # Check API keys
    print("\n" + "=" * 80)
    print("API Key Status for Email Parsing Workflow:")
    
    current_provider = EmailParsingModelConfig.get_provider()
    api_key_mapping = {
        ModelProvider.OPENAI: "OPENAI_API_KEY",
        ModelProvider.ANTHROPIC: "ANTHROPIC_API_KEY",
        ModelProvider.GEMINI: "GEMINI_API_KEY",
        ModelProvider.BEDROCK: "BEDROCK_AWS_ACCESS_KEY_ID",
        ModelProvider.OLLAMA: "OLLAMA_BASE_URL",
        ModelProvider.AZURE_OPENAI: "AZURE_OPENAI_API_KEY"
    }
    
    for provider, key_name in api_key_mapping.items():
        value = os.getenv(key_name)
        status = "✓" if value else "✗"
        current = " (CURRENT)" if provider == current_provider else ""
        
        if value and len(value) > 10:
            masked = value[:10] + "..."
        elif value:
            masked = "***"
        else:
            masked = "Not set"
            
        print(f"  {provider.value}: {status} {masked}{current}")


def test_model_switching():
    """Test switching models at runtime"""
    print("\n" + "=" * 80)
    print("Testing Model Switching")
    print("=" * 80)
    
    # Save current settings
    original_provider = os.getenv("EMAIL_PARSING_MODEL_PROVIDER")
    
    # Test switching providers
    test_providers = ["anthropic", "openai", "gemini"]
    
    for provider_name in test_providers:
        os.environ["EMAIL_PARSING_MODEL_PROVIDER"] = provider_name
        provider, model = EmailParsingModelConfig.get_model('classification')
        print(f"\nProvider: {provider_name}")
        print(f"  Classification Model: {model}")
        
        provider, model = EmailParsingModelConfig.get_model('extraction')
        print(f"  Extraction Model: {model}")
    
    # Restore original
    if original_provider:
        os.environ["EMAIL_PARSING_MODEL_PROVIDER"] = original_provider
    else:
        os.environ.pop("EMAIL_PARSING_MODEL_PROVIDER", None)


if __name__ == "__main__":
    test_workflow_config()
    test_model_switching()