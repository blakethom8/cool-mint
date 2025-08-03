"""Entity matching service package

This package provides a unified interface for matching various entity types
including contacts, provider groups, and sites of service.
"""

# Import main service interface
from .entity_matching_service import EntityMatchingService

# Import match result types
from .models.match_results import (
    MatchResult,
    ContactMatch,
    ProviderGroupMatch,
    SiteOfServiceMatch,
    MatchContext,
    EntityType,
    MatchType
)

# Import base classes for extension
from .base import BaseEntityMatcher, MatcherRegistry, MatchingConfig

# Import utilities
from .utils.scoring import MatchScorer, ScoringResult
from .utils.text_utils import TextSimilarity, NameNormalizer, PhoneNormalizer
from .utils.name_parser import NameParser, ParsedName

__all__ = [
    # Main service
    'EntityMatchingService',
    
    # Result types
    'MatchResult',
    'ContactMatch',
    'ProviderGroupMatch',
    'SiteOfServiceMatch',
    'MatchContext',
    'EntityType',
    'MatchType',
    
    # Base classes
    'BaseEntityMatcher',
    'MatcherRegistry',
    'MatchingConfig',
    
    # Utilities
    'MatchScorer',
    'ScoringResult',
    'TextSimilarity',
    'NameNormalizer',
    'PhoneNormalizer',
    'NameParser',
    'ParsedName',
]