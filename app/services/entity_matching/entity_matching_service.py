"""Main entity matching service interface"""
from typing import List, Optional, Dict, Any, Union
from sqlalchemy.orm import Session
import logging

from .base import MatcherRegistry, BaseEntityMatcher
from .models.match_results import (
    MatchResult, ContactMatch, ProviderGroupMatch, 
    SiteOfServiceMatch, MatchContext, EntityType
)
from .utils.scoring import MatchScorer

# Import matchers to register them
from .matchers import contact_matcher

logger = logging.getLogger(__name__)


class EntityMatchingService:
    """
    Unified service for matching entities across different types
    
    This service provides a single interface for matching contacts,
    provider groups, sites of service, and other entities.
    """
    
    def __init__(self, session: Optional[Session] = None):
        """
        Initialize the entity matching service
        
        Args:
            session: Optional SQLAlchemy session. If not provided,
                    matchers will create their own sessions.
        """
        self.session = session
        self.scorer = MatchScorer()
        self._matcher_cache = {}
    
    def match(self, query: str, entity_type: Union[str, EntityType], 
             context: Optional[Union[Dict, MatchContext]] = None,
             with_scoring: bool = True) -> List[MatchResult]:
        """
        Main entry point for entity matching
        
        Args:
            query: Search query (name, email, identifier, etc.)
            entity_type: Type of entity to match
            context: Optional context for better matching
            with_scoring: Whether to apply scoring and ranking
            
        Returns:
            List of match results sorted by confidence
        """
        if not query or not query.strip():
            return []
        
        # Convert string to EntityType if needed
        if isinstance(entity_type, str):
            try:
                entity_type = EntityType(entity_type)
            except ValueError:
                logger.error(f"Invalid entity type: {entity_type}")
                return []
        
        # Convert dict to MatchContext if needed
        if isinstance(context, dict):
            context = MatchContext(**context)
        
        # Get appropriate matcher
        try:
            matcher = self._get_matcher(entity_type)
        except ValueError as e:
            logger.error(f"Failed to get matcher: {e}")
            return []
        
        # Perform matching
        matches = matcher.match(query, context)
        
        # Apply scoring if requested
        if with_scoring and matches:
            scored_matches = self.scorer.rank_matches(matches, query, context)
            return [match for match, score in scored_matches]
        
        return matches
    
    def match_contact(self, query: str, 
                     context: Optional[Union[Dict, MatchContext]] = None,
                     with_scoring: bool = True) -> List[ContactMatch]:
        """
        Convenience method for contact matching
        
        Args:
            query: Search query
            context: Optional context
            with_scoring: Whether to apply scoring
            
        Returns:
            List of ContactMatch results
        """
        matches = self.match(query, EntityType.CONTACT, context, with_scoring)
        # Type narrowing - we know these are ContactMatch objects
        return [m for m in matches if isinstance(m, ContactMatch)]
    
    def match_provider_group(self, query: str,
                           context: Optional[Union[Dict, MatchContext]] = None,
                           with_scoring: bool = True) -> List[ProviderGroupMatch]:
        """
        Convenience method for provider group matching
        
        Args:
            query: Search query
            context: Optional context
            with_scoring: Whether to apply scoring
            
        Returns:
            List of ProviderGroupMatch results
        """
        matches = self.match(query, EntityType.PROVIDER_GROUP, context, with_scoring)
        return [m for m in matches if isinstance(m, ProviderGroupMatch)]
    
    def match_site(self, query: str,
                  context: Optional[Union[Dict, MatchContext]] = None,
                  with_scoring: bool = True) -> List[SiteOfServiceMatch]:
        """
        Convenience method for site of service matching
        
        Args:
            query: Search query
            context: Optional context
            with_scoring: Whether to apply scoring
            
        Returns:
            List of SiteOfServiceMatch results
        """
        matches = self.match(query, EntityType.SITE_OF_SERVICE, context, with_scoring)
        return [m for m in matches if isinstance(m, SiteOfServiceMatch)]
    
    def match_multiple(self, query: str,
                      entity_types: List[Union[str, EntityType]],
                      context: Optional[Union[Dict, MatchContext]] = None,
                      with_scoring: bool = True) -> Dict[str, List[MatchResult]]:
        """
        Match across multiple entity types
        
        Args:
            query: Search query
            entity_types: List of entity types to search
            context: Optional context
            with_scoring: Whether to apply scoring
            
        Returns:
            Dictionary mapping entity type to match results
        """
        results = {}
        
        for entity_type in entity_types:
            matches = self.match(query, entity_type, context, with_scoring)
            if matches:
                type_key = entity_type.value if isinstance(entity_type, EntityType) else entity_type
                results[type_key] = matches
        
        return results
    
    def get_best_match(self, query: str, entity_type: Union[str, EntityType],
                      context: Optional[Union[Dict, MatchContext]] = None,
                      min_confidence: float = 0.7) -> Optional[MatchResult]:
        """
        Get the single best match if it meets confidence threshold
        
        Args:
            query: Search query
            entity_type: Type of entity to match
            context: Optional context
            min_confidence: Minimum confidence threshold
            
        Returns:
            Best match or None if no match meets threshold
        """
        matches = self.match(query, entity_type, context, with_scoring=True)
        
        if matches and matches[0].confidence_score >= min_confidence:
            return matches[0]
        
        return None
    
    def _get_matcher(self, entity_type: EntityType) -> BaseEntityMatcher:
        """Get or create a matcher for the entity type"""
        # Check cache first
        if entity_type in self._matcher_cache:
            return self._matcher_cache[entity_type]
        
        # Create new matcher
        matcher = MatcherRegistry.get_matcher(entity_type.value, self.session)
        
        # Cache it if we're managing the session
        if self.session:
            self._matcher_cache[entity_type] = matcher
        
        return matcher
    
    def close(self):
        """Close any cached matchers"""
        for matcher in self._matcher_cache.values():
            matcher.close()
        self._matcher_cache.clear()
    
    def __enter__(self):
        """Context manager support"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup"""
        self.close()
    
    @staticmethod
    def list_supported_entities() -> List[str]:
        """List all supported entity types"""
        return MatcherRegistry.list_matchers()