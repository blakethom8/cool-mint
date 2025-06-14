from pathlib import Path
import yaml
import frontmatter
from jinja2 import Environment, FileSystemLoader, StrictUndefined, TemplateError, meta
from dataclasses import dataclass
from typing import Optional

"""
Prompt Management Module

This module provides functionality for loading and rendering prompt templates with frontmatter.
It uses Jinja2 for template rendering and python-frontmatter for metadata handling,
implementing a singleton pattern for template environment management.
"""


@dataclass
class ModelConfig:
    """Data class for model configuration."""

    provider: str
    name: str


@dataclass
class PromptData:
    """Data class for storing prompt information."""

    system_prompt: str
    model: ModelConfig


class PromptManager:
    """Manager class for handling prompt templates and their metadata.

    This class provides functionality to load prompt templates from files,
    render them with variables, and extract template metadata and requirements.
    It implements a singleton pattern for the Jinja2 environment to ensure
    consistent template loading across the application.

    Attributes:
        _env: Class-level singleton instance of Jinja2 Environment

    Example:
        # Render a prompt template with variables
        prompt = PromptManager.get_prompt("greeting", name="Alice")

        # Get template metadata and required variables
        info = PromptManager.get_template_info("greeting")
    """

    _env = None

    @classmethod
    def _get_env(cls, templates_dir="prompts") -> Environment:
        """Gets or creates the Jinja2 environment singleton.

        Args:
            templates_dir: Directory name containing prompt templates, relative to app/

        Returns:
            Configured Jinja2 Environment instance

        Note:
            Uses StrictUndefined to raise errors for undefined variables,
            helping catch template issues early.
        """
        templates_dir = Path(__file__).parent.parent / templates_dir
        if cls._env is None:
            cls._env = Environment(
                loader=FileSystemLoader(templates_dir),
                undefined=StrictUndefined,
            )
        return cls._env

    def get_prompt(self, template: str, **kwargs) -> PromptData:
        """Loads and renders a prompt template with provided variables.

        Args:
            template: Name of the template file (without extension)
            **kwargs: Variables to use in template rendering

        Returns:
            PromptData object containing system_prompt and model info

        Raises:
            ValueError: If template rendering fails
            FileNotFoundError: If template file doesn't exist
        """
        env = self._get_env()
        base_path = Path(env.loader.searchpath[0]) / template

        # Try loading as YAML first
        yaml_path = base_path.with_suffix(".yaml")
        if yaml_path.exists():
            with open(yaml_path) as file:
                data = yaml.safe_load(file)
                return PromptData(
                    system_prompt=data["system_prompt"],
                    model=ModelConfig(**data["model"]),
                )

        # Fall back to J2 template
        template_path = f"{template}.j2"
        with open(env.loader.get_source(env, template_path)[1]) as file:
            post = frontmatter.load(file)

        template = env.from_string(post.content)
        try:
            rendered = template.render(**kwargs)
            model_data = post.get("model", {})
            return PromptData(system_prompt=rendered, model=ModelConfig(**model_data))
        except TemplateError as e:
            raise ValueError(f"Error rendering template: {str(e)}")

    @staticmethod
    def get_template_info(template: str) -> dict:
        """Extracts metadata and variable requirements from a template.

        Args:
            template: Name of the template file (without extension)

        Returns:
            Dictionary containing:
                - name: Template name
                - description: Template description from frontmatter
                - author: Template author from frontmatter
                - variables: List of required template variables
                - frontmatter: Raw frontmatter metadata dictionary

        Raises:
            FileNotFoundError: If template file doesn't exist
        """
        env = PromptManager._get_env()
        template_path = f"{template}.j2"
        with open(env.loader.get_source(env, template_path)[1]) as file:
            post = frontmatter.load(file)

        ast = env.parse(post.content)
        variables = meta.find_undeclared_variables(ast)

        return {
            "name": template,
            "description": post.metadata.get("description", "No description provided"),
            "author": post.metadata.get("author", "Unknown"),
            "variables": list(variables),
            "frontmatter": post.metadata,
        }
