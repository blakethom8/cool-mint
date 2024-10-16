# LLM Factory and Provider System

This module implements a flexible system for integrating various Language Model (LLM) providers
using a factory pattern. It currently supports OpenAI, Anthropic, and a local Llama model
through Ollama, but can be easily extended to support additional providers.

## How it works

1. The LLMFactory class acts as the main entry point for creating and using LLM providers.
2. Each provider (e.g., OpenAI, Anthropic, Llama) is implemented as a separate class
   inheriting from the abstract LLMProvider base class.
3. The factory determines which provider to use based on the input and creates the
   appropriate provider instance.
4. All providers implement a common interface, allowing for consistent usage across
   different LLM backends.
5. We use the Instructor library to patch all providers, enabling structured output
   with Pydantic models. This allows for type-safe and validated responses from the LLMs.

## Implementing a new provider

To add support for a new LLM provider, follow these steps:
1. Create a new class that inherits from LLMProvider.
2. Implement the required methods: __init__, _initialize_client, and create_completion.
3. Use Instructor to patch the client in the _initialize_client method.
4. Add the new provider to the providers dictionary in the LLMFactory._create_provider method.

Example usage:
```python
factory = LLMFactory("openai")
response = factory.create_completion(ResponseModel, messages, **kwargs)
```

Available providers:
- OpenAI: Uses the OpenAI API for models like GPT-3.5 and GPT-4.
- Anthropic: Integrates with Anthropic's Claude models.
- Llama: An example implementation for running Llama models locally using Ollama.

Note: The Llama provider is an example of how to integrate a local model. Make sure you have
Ollama set up and running to use this provider.

## Structured Output
By using Instructor, all providers are patched to support structured output using Pydantic models. This enables type-safe and validated responses from the LLMs, improving reliability and ease of use.