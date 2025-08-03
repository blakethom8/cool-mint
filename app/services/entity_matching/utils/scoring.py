"""Scoring utilities for entity matching"""
from typing import Dict, Optional, List
from dataclasses import dataclass

from ..models.match_results import MatchResult, MatchType, MatchContext
from ..base import MatchingConfig


@dataclass
class ScoringResult:
    """Detailed scoring information"""
    base_score: float
    adjustments: Dict[str, float]
    final_score: float
    explanation: str
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'base_score': round(self.base_score, 3),
            'adjustments': {k: round(v, 3) for k, v in self.adjustments.items()},
            'final_score': round(self.final_score, 3),
            'explanation': self.explanation
        }


class MatchScorer:
    """Score and rank entity matches"""
    
    def __init__(self, config: Optional[MatchingConfig] = None):
        """
        Initialize scorer with optional configuration
        
        Args:
            config: Matching configuration, uses defaults if not provided
        """
        self.config = config or MatchingConfig()
    
    def score_match(self, match: MatchResult, query: str, 
                   context: Optional[MatchContext] = None) -> ScoringResult:
        """
        Calculate comprehensive score for a match
        
        Args:
            match: The match result to score
            query: Original search query
            context: Optional context for boosting
            
        Returns:
            ScoringResult with detailed scoring information
        """
        adjustments = {}
        explanations = []
        
        # Get base score from match type
        base_score = self._get_base_score(match.match_type)
        explanations.append(f"{match.match_type.value} match (base: {base_score:.2f})")
        
        # Apply context boosts
        if context:
            context_adj = self._apply_context_boosts(match, context)
            if context_adj:
                adjustments.update(context_adj)
                for boost_type, boost_value in context_adj.items():
                    explanations.append(f"{boost_type} (+{boost_value:.2f})")
        
        # Apply activity status adjustment
        if not match.active:
            penalty = -self.config.INACTIVE_PENALTY
            adjustments['inactive_penalty'] = penalty
            explanations.append(f"Inactive entity ({penalty:.2f})")
        
        # Calculate final score
        total_adjustments = sum(adjustments.values())
        final_score = min(base_score + total_adjustments, 1.0)
        final_score = max(final_score, 0.0)  # Ensure non-negative
        
        return ScoringResult(
            base_score=base_score,
            adjustments=adjustments,
            final_score=final_score,
            explanation=' | '.join(explanations)
        )
    
    def _get_base_score(self, match_type: MatchType) -> float:
        """Get base score for a match type"""
        return self.config.MATCH_TYPE_WEIGHTS.get(
            match_type.value, 
            0.5  # Default for unknown match types
        )
    
    def _apply_context_boosts(self, match: MatchResult, 
                             context: MatchContext) -> Dict[str, float]:
        """Apply context-based score boosts"""
        boosts = {}
        
        # Organization match boost
        if context.organization and hasattr(match, 'organization'):
            if match.organization and self._matches_organization(
                context.organization, match.organization
            ):
                boosts['organization_boost'] = self.config.CONTEXT_BOOSTS['organization_match']
        
        # Specialty match boost (for contacts)
        if context.specialty and hasattr(match, 'specialty'):
            if match.specialty and self._matches_specialty(
                context.specialty, match.specialty
            ):
                boosts['specialty_boost'] = self.config.CONTEXT_BOOSTS['specialty_match']
        
        # Location match boost (for sites)
        if context.location:
            location_match = False
            
            # Check various location fields
            if hasattr(match, 'city') and match.city:
                if context.location.lower() in match.city.lower():
                    location_match = True
            elif hasattr(match, 'primary_location') and match.primary_location:
                if context.location.lower() in match.primary_location.lower():
                    location_match = True
            
            if location_match:
                boosts['location_boost'] = self.config.CONTEXT_BOOSTS['location_match']
        
        return boosts
    
    def _matches_organization(self, context_org: str, entity_org: str) -> bool:
        """Check if organizations match"""
        context_lower = context_org.lower()
        entity_lower = entity_org.lower()
        
        # Exact match
        if context_lower == entity_lower:
            return True
        
        # Contains match
        if context_lower in entity_lower or entity_lower in context_lower:
            return True
        
        # Token overlap
        context_tokens = set(context_lower.split())
        entity_tokens = set(entity_lower.split())
        
        # Significant overlap (at least 50% of tokens match)
        if context_tokens & entity_tokens:
            overlap = len(context_tokens & entity_tokens)
            min_tokens = min(len(context_tokens), len(entity_tokens))
            if overlap / min_tokens >= 0.5:
                return True
        
        return False
    
    def _matches_specialty(self, context_spec: str, entity_spec: str) -> bool:
        """Check if specialties match"""
        context_lower = context_spec.lower()
        entity_lower = entity_spec.lower()
        
        # Exact match
        if context_lower == entity_lower:
            return True
        
        # Related specialties
        specialty_groups = {
            'cardiology': ['cardiology', 'cardiac', 'heart', 'cardiovascular'],
            'oncology': ['oncology', 'cancer', 'hematology', 'radiation'],
            'orthopedics': ['orthopedic', 'orthopaedic', 'sports medicine', 'spine'],
            'neurology': ['neurology', 'neurosurgery', 'neurological'],
            'internal medicine': ['internal medicine', 'internist', 'hospitalist'],
            'surgery': ['surgery', 'surgical', 'surgeon'],
            'pediatrics': ['pediatrics', 'pediatric', 'children'],
            'psychiatry': ['psychiatry', 'psychiatric', 'mental health', 'behavioral']
        }
        
        # Check if both specialties are in the same group
        for group, related in specialty_groups.items():
            context_in_group = any(s in context_lower for s in related)
            entity_in_group = any(s in entity_lower for s in related)
            
            if context_in_group and entity_in_group:
                return True
        
        return False
    
    def rank_matches(self, matches: List[MatchResult], query: str,
                    context: Optional[MatchContext] = None) -> List[tuple[MatchResult, ScoringResult]]:
        """
        Rank matches by comprehensive scoring
        
        Args:
            matches: List of matches to rank
            query: Original search query
            context: Optional context for scoring
            
        Returns:
            List of (match, score) tuples sorted by score
        """
        scored_matches = []
        
        for match in matches:
            score = self.score_match(match, query, context)
            if score.final_score >= self.config.MIN_CONFIDENCE_THRESHOLD:
                scored_matches.append((match, score))
        
        # Sort by final score descending
        scored_matches.sort(key=lambda x: x[1].final_score, reverse=True)
        
        # Limit results
        return scored_matches[:self.config.MAX_RESULTS]