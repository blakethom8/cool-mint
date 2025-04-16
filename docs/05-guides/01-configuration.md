# Configuration Management

The configuration system in GenAI Launchpad uses Pydantic Settings for robust, type-safe configuration management. This approach ensures that all configuration values are validated at startup, preventing runtime errors due to misconfiguration.

## Configuration Architecture

The configuration system is built around a hierarchical structure where settings.py serves as the central configuration hub. Each major component has its own configuration class, all of which are composed into the main Settings class.

```python
class Settings(BaseSettings):
    app_name: str = "GenAI Project Template"
    llm: LLMConfig = LLMConfig()
    database: DatabaseConfig = DatabaseConfig()
```

## Core Configuration Components

### LLM Configuration (llm_config.py)

The LLM configuration manages settings for different AI providers. It implements a provider-specific configuration pattern:

```python
class LLMConfig(BaseSettings):
    openai: OpenAISettings = OpenAISettings()
    anthropic: AnthropicSettings = AnthropicSettings()
    llama: LlamaSettings = LlamaSettings()
```

Each provider has its own settings class with specific configurations:

```python
class OpenAISettings(LLMProviderSettings):
    api_key: str = os.getenv("OPENAI_API_KEY")
    default_model: str = "gpt-4"
    embedding_model: str = "text-embedding-3-small"
```

### Celery Configuration (celery_config.py)

The Celery configuration manages the task queue settings, providing a clean interface for Celery setup:

```python
@lru_cache
def get_celery_config():
    redis_url = get_redis_url()
    return {
        "broker_url": redis_url,
        "result_backend": redis_url,
        "task_serializer": "json",
        "accept_content": ["json"]
    }
```

## Environment Variable Management

The configuration system integrates with environment variables through Python-dotenv:

```python
from dotenv import load_dotenv
load_dotenv()
```

This allows for different configuration files per environment if needed:

- `.env` for local development
- `.env.staging` for staging environment
- `.env.production` for production environment

## Configuration Best Practices

### Caching Configuration

We use Python's lru_cache to prevent repeated parsing of configuration files:

```python
@lru_cache
def get_settings() -> Settings:
    return Settings()
```

## Security Considerations

The configuration system implements several security best practices:

1. Sensitive values are never hardcoded
2. API keys are loaded from environment variables
3. Different configurations for different environments
4. Validation of security-critical settings at startup