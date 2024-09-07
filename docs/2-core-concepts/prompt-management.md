# Managing Prompt Templates with Jinja

## Introduction

This guide explains how to effectively manage and use prompt templates in your AI applications using Jinja2, a powerful and flexible templating engine for Python. By leveraging Jinja2 for prompt management, you can create dynamic, reusable, and easily maintainable prompts for your large language model (LLM) applications.

## Table of Contents

- [Managing Prompt Templates with Jinja](#managing-prompt-templates-with-jinja)
  - [Introduction](#introduction)
  - [Table of Contents](#table-of-contents)
  - [Project Structure](#project-structure)
  - [Understanding the Prompt Manager](#understanding-the-prompt-manager)
  - [Creating Jinja Templates](#creating-jinja-templates)
  - [Using Prompt Templates](#using-prompt-templates)
  - [Advanced Jinja Features](#advanced-jinja-features)
    - [1. Conditionals](#1-conditionals)
    - [2. Loops](#2-loops)
    - [3. Filters](#3-filters)
    - [4. Macros](#4-macros)
    - [5. Template Inheritance](#5-template-inheritance)
  - [Benefits of This Approach](#benefits-of-this-approach)
    - [Jinja vs. External Databases for Prompt Management](#jinja-vs-external-databases-for-prompt-management)
  - [Best Practices](#best-practices)

## Project Structure

The prompt management system is organized as follows:

```text
prompts/
├── __init__.py
├── prompt_manager.py
└── templates/
    ├── prompt_template.jinja
```

- `prompt_manager.py`: Contains the `PromptManager` class for handling prompt templates.
- `templates/`: Directory containing Jinja template files (`.jinja` extension).

## Understanding the Prompt Manager

The `PromptManager` class in `prompt_manager.py` is the core component for working with prompt templates. Here's an overview of its key methods:

1. `get_env()`: Sets up the Jinja environment, specifying the template directory and configuration.
2. `get_prompt()`: Renders a specific template with provided variables.
3. `get_template_info()`: Retrieves metadata and variable information for a given template.

## Creating Jinja Templates

Jinja templates are stored in the `prompts/templates/` directory with a `.jinja` extension. Each template consists of two parts:

1. **Frontmatter**: YAML-formatted metadata at the beginning of the file.
2. **Template Content**: The main body of the template using Jinja syntax.

Example (`ticket_analysis.jinja`):

```jinja
---
description: A template for analyzing incoming {{ pipeline | default('customer support') }} tickets
author: TechGear AI Team
---
You're an AI assistant named {{ name | default('Emma') }}, working for {{ company | default('TechGear') }}.
Your goal is to analyze incoming {{ pipeline | default('support') }} tickets and classify their intent.

# CONTEXT
You will be provided with the following information from a {{ pipeline | default('support') }} ticket:
- Sender: The name or identifier of the person who sent the ticket
- Subject: The subject line of the ticket
- Body: The main content of the ticket

# TASK
Your task is to analyze the ticket and determine its primary intent. You should also provide a confidence score for your classification and explain your reasoning.

{% if pipeline == 'helpdesk' %}
# ADDITIONAL CONTEXT FOR INTERNAL HELPDESK
As this is an internal helpdesk ticket, consider the following:
- The sender is a TechGear employee
- Prioritize issues related to internal systems, software, or hardware
- Be aware of potential sensitive or confidential information
{% else %}
# ADDITIONAL CONTEXT FOR CUSTOMER SUPPORT
As this is a customer support ticket, consider the following:
- The sender is a TechGear customer or user
- Focus on product-related issues, billing inquiries, or general customer service matters
- Maintain a customer-centric approach in your analysis
{% endif %}

# INPUT
New ticket: {{ ticket }}
```

## Using Prompt Templates

To use a prompt template in your code:

```python
from prompts.prompt_manager import PromptManager

# Render a template
support_prompt = PromptManager.get_prompt(
    "ticket_analysis",
    pipeline="support",
    ticket={"sender": "John Doe", "subject": "Login Issue", "body": "I can't log in to my account."}
)

# Get template information
template_info = PromptManager.get_template_info("ticket_analysis")
```

## Advanced Jinja Features

Jinja2 offers several advanced features for creating flexible and powerful templates:

### 1. Conditionals

Use `if`, `elif`, and `else` statements to include or exclude content based on conditions:

```jinja
{% if pipeline == 'helpdesk' %}
    # Helpdesk-specific instructions
{% elif pipeline == 'sales' %}
    # Sales-specific instructions
{% else %}
    # Default instructions
{% endif %}
```

### 2. Loops

Iterate over lists or dictionaries to generate repetitive content:

```jinja
{% for step in troubleshooting_steps %}
    {{ loop.index }}. {{ step }}
{% endfor %}
```

### 3. Filters

Apply transformations to variables:

```jinja
{{ user_name | capitalize }}
{{ product_list | join(', ') }}
{{ description | truncate(100) }}
```

### 4. Macros

Create reusable template snippets:

```jinja
{% macro format_price(amount) -%}
    ${{ "%.2f"|format(amount) }}
{%- endmacro %}

Product price: {{ format_price(product.price) }}
```

### 5. Template Inheritance

Create base templates and extend them:

```jinja
{# base_prompt.jinja #}
# SYSTEM INSTRUCTION
{{ system_instruction }}

# USER INPUT
{{ user_input }}

# ASSISTANT RESPONSE
{% block response %}{% endblock %}

{# specific_prompt.jinja #}
{% extends "base_prompt.jinja" %}

{% block response %}
Here is my response to your query:
1. ...
2. ...
3. ...
{% endblock %}
```

## Benefits of This Approach

1. **Modularity**: Separates prompt logic from application code, improving maintainability.
2. **Reusability**: Templates can be shared across different parts of your application.
3. **Version Control**: Easy to track changes and manage different versions of prompts.
4. **Dynamic Content**: Allows for context-specific prompt generation.
5. **Reduced Token Usage**: Templates can be optimized to minimize unnecessary content, reducing API costs.
6. **Consistency**: Ensures a unified approach to prompt structure across your application.
7. **Rapid Iteration**: Quickly test and refine prompts without modifying application code.

### Jinja vs. External Databases for Prompt Management

While external databases can be used for prompt management, the Jinja-based approach offers several advantages:

1. **Performance**: In-memory template rendering is faster than database queries.
2. **Simplicity**: No need for additional infrastructure or database management.
3. **Version Control Integration**: Templates can be easily versioned alongside code.
4. **Offline Capability**: Templates work without an active database connection.
5. **Developer-Friendly**: Jinja syntax is familiar to many developers and easy to learn.

## Best Practices

1. **Use Clear Template Names**: Choose descriptive names for your templates (e.g., `customer_support_greeting.jinja`).
2. **Leverage Frontmatter**: Include metadata like description, author, and version in the template frontmatter.
3. **Modularize Templates**: Break down complex prompts into smaller, reusable components.
4. **Comment Your Templates**: Add comments to explain complex logic or variable usage.
5. **Validate Inputs**: Use Jinja's `StrictUndefined` to catch missing variables early.
6. **Optimize for Token Usage**: Structure templates to minimize unnecessary whitespace and repetition.
7. **Regular Review**: Periodically review and update templates to ensure they align with current best practices and model capabilities.

By following these guidelines and leveraging the power of Jinja templates, you can create a flexible, maintainable, and efficient prompt management system for your AI applications. This approach allows you to focus on crafting effective prompts while keeping your codebase clean and organized.
