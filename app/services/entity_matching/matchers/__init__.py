"""Entity matchers package

This package contains specific matcher implementations for different entity types.
Each matcher is automatically registered when imported.
"""

# Import all matchers to ensure they get registered
from .contact_matcher import ContactMatcher

__all__ = [
    'ContactMatcher',
]