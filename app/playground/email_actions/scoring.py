"""Scoring and ranking logic for contact matches"""
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from difflib import SequenceMatcher
import re
from collections import Counter


@dataclass
class MatchScore:
    """Detailed scoring information for a match"""
    total_score: float
    components: Dict[str, float]
    explanation: str
    
    def to_dict(self) -> Dict:
        return {
            'total': round(self.total_score, 3),
            'components': {k: round(v, 3) for k, v in self.components.items()},
            'explanation': self.explanation
        }


class ContactScorer:
    """Score and rank contact matches"""
    
    def __init__(self):
        # Weights for different match types
        self.weights = {
            'email_exact': 1.0,
            'npi_exact': 1.0,
            'external_id_exact': 1.0,
            'name_exact': 0.95,
            'first_last_exact': 0.9,
            'last_name_only': 0.7,
            'fuzzy_name': 0.8,
            'organization_match': 0.15,
            'specialty_relevance': 0.1,
            'phone_match': 0.85,
            'active_contact': 0.05,
            'recent_activity': 0.05
        }
    
    def calculate_match_score(self, query: str, contact: Dict, 
                            match_type: str, context: Optional[Dict] = None) -> MatchScore:
        """Calculate comprehensive match score"""
        components = {}
        explanations = []
        
        # Base score from match type
        base_score = self.weights.get(match_type, 0.5)
        components['base'] = base_score
        explanations.append(f"{match_type} match (base: {base_score})")
        
        # Additional scoring based on context
        if context:
            # Organization match
            if context.get('organization') and contact.get('organization'):
                org_score = self._score_organization_match(
                    context['organization'], 
                    contact['organization']
                )
                if org_score > 0:
                    components['organization'] = org_score * self.weights['organization_match']
                    explanations.append(f"Organization match (+{components['organization']:.2f})")
            
            # Specialty relevance
            if context.get('specialty') and contact.get('specialty'):
                spec_score = self._score_specialty_match(
                    context['specialty'],
                    contact['specialty']
                )
                if spec_score > 0:
                    components['specialty'] = spec_score * self.weights['specialty_relevance']
                    explanations.append(f"Specialty match (+{components['specialty']:.2f})")
        
        # Active contact bonus
        if contact.get('active', True):
            components['active'] = self.weights['active_contact']
            explanations.append(f"Active contact (+{components['active']:.2f})")
        
        # Recent activity bonus
        if contact.get('last_activity_days') is not None:
            if contact['last_activity_days'] < 90:
                components['recent'] = self.weights['recent_activity']
                explanations.append(f"Recent activity (+{components['recent']:.2f})")
        
        # Calculate total
        total_score = sum(components.values())
        
        # Apply penalties
        penalties = self._calculate_penalties(query, contact, match_type)
        if penalties:
            total_score *= (1 - sum(penalties.values()))
            for penalty_type, penalty_value in penalties.items():
                explanations.append(f"{penalty_type} penalty (-{penalty_value:.2f})")
        
        # Cap at 1.0
        total_score = min(total_score, 1.0)
        
        return MatchScore(
            total_score=total_score,
            components=components,
            explanation=' | '.join(explanations)
        )
    
    def _score_organization_match(self, query_org: str, contact_org: str) -> float:
        """Score organization match"""
        if not query_org or not contact_org:
            return 0.0
        
        query_lower = query_org.lower()
        contact_lower = contact_org.lower()
        
        # Exact match
        if query_lower == contact_lower:
            return 1.0
        
        # Contains match
        if query_lower in contact_lower or contact_lower in query_lower:
            return 0.8
        
        # Token overlap
        query_tokens = set(query_lower.split())
        contact_tokens = set(contact_lower.split())
        
        if query_tokens & contact_tokens:
            overlap = len(query_tokens & contact_tokens)
            total = len(query_tokens | contact_tokens)
            return overlap / total if total > 0 else 0
        
        return 0.0
    
    def _score_specialty_match(self, query_spec: str, contact_spec: str) -> float:
        """Score specialty relevance"""
        if not query_spec or not contact_spec:
            return 0.0
        
        query_lower = query_spec.lower()
        contact_lower = contact_spec.lower()
        
        # Exact match
        if query_lower == contact_lower:
            return 1.0
        
        # Related specialties
        specialty_groups = {
            'cardiology': ['cardiology', 'cardiac', 'heart', 'cardiovascular'],
            'oncology': ['oncology', 'cancer', 'hematology', 'radiation'],
            'orthopedics': ['orthopedic', 'orthopaedic', 'sports medicine', 'spine'],
            'neurology': ['neurology', 'neurosurgery', 'neurological'],
            'internal medicine': ['internal medicine', 'internist', 'hospitalist']
        }
        
        for group, related in specialty_groups.items():
            if any(s in query_lower for s in related) and any(s in contact_lower for s in related):
                return 0.8
        
        return 0.0
    
    def _calculate_penalties(self, query: str, contact: Dict, match_type: str) -> Dict[str, float]:
        """Calculate penalties for the match"""
        penalties = {}
        
        # Inactive contact penalty
        if not contact.get('active', True):
            penalties['inactive'] = 0.2
        
        # No email penalty (for non-email matches)
        if match_type != 'email_exact' and not contact.get('email'):
            penalties['no_email'] = 0.1
        
        # Fuzzy match quality penalty
        if match_type == 'fuzzy_name' and 'similarity' in contact:
            if contact['similarity'] < 0.7:
                penalties['low_similarity'] = 0.2
        
        return penalties
    
    def rank_matches(self, matches: List[Tuple[Dict, str, float]],
                    query: str, context: Optional[Dict] = None) -> List[Tuple[Dict, MatchScore]]:
        """Rank matches by comprehensive scoring"""
        scored_matches = []
        
        for contact, match_type, base_confidence in matches:
            score = self.calculate_match_score(query, contact, match_type, context)
            scored_matches.append((contact, score))
        
        # Sort by total score descending
        scored_matches.sort(key=lambda x: x[1].total_score, reverse=True)
        
        return scored_matches
    
    def explain_score(self, score: MatchScore) -> str:
        """Generate human-readable explanation of score"""
        explanation = [f"Total score: {score.total_score:.3f}"]
        
        # Sort components by value
        sorted_components = sorted(
            score.components.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        for component, value in sorted_components:
            if value > 0:
                explanation.append(f"  • {component}: +{value:.3f}")
        
        if score.explanation:
            explanation.append(f"\nDetails: {score.explanation}")
        
        return '\n'.join(explanation)


# Utility class for advanced string matching
class StringMatcher:
    """Advanced string matching algorithms"""
    
    @staticmethod
    def token_set_ratio(str1: str, str2: str) -> float:
        """Token set ratio - order doesn't matter"""
        tokens1 = set(str1.lower().split())
        tokens2 = set(str2.lower().split())
        
        if not tokens1 or not tokens2:
            return 0.0
        
        intersection = tokens1 & tokens2
        union = tokens1 | tokens2
        
        return len(intersection) / len(union) if union else 0.0
    
    @staticmethod
    def partial_ratio(str1: str, str2: str) -> float:
        """Find best partial match"""
        if not str1 or not str2:
            return 0.0
        
        shorter = str1 if len(str1) <= len(str2) else str2
        longer = str2 if len(str1) <= len(str2) else str1
        
        matcher = SequenceMatcher(None, shorter.lower(), longer.lower())
        return matcher.ratio()
    
    @staticmethod
    def weighted_ratio(str1: str, str2: str) -> float:
        """Weighted combination of different ratios"""
        # Simple ratio
        simple = SequenceMatcher(None, str1.lower(), str2.lower()).ratio()
        
        # Token set ratio
        token_set = StringMatcher.token_set_ratio(str1, str2)
        
        # Partial ratio
        partial = StringMatcher.partial_ratio(str1, str2)
        
        # Weighted average
        return (simple * 0.5 + token_set * 0.3 + partial * 0.2)


# Test scoring functionality
def test_scoring():
    """Test the scoring system"""
    scorer = ContactScorer()
    
    # Sample contact
    contact = {
        'name': 'Dr. Sarah Johnson',
        'email': 'sarah.johnson@cedars.org',
        'organization': 'Cedars-Sinai Medical Center',
        'specialty': 'Cardiology',
        'active': True,
        'last_activity_days': 30
    }
    
    # Test scenarios
    test_cases = [
        ("Dr. Johnson", "last_name_only", {'organization': 'Cedars-Sinai'}),
        ("Sarah Johnson", "name_exact", None),
        ("sara jonson", "fuzzy_name", {'specialty': 'Cardiac Surgery'}),
        ("sarah.johnson@cedars.org", "email_exact", None)
    ]
    
    print("Contact Scoring Test Results")
    print("=" * 60)
    
    for query, match_type, context in test_cases:
        print(f"\nQuery: '{query}' | Type: {match_type}")
        if context:
            print(f"Context: {context}")
        
        score = scorer.calculate_match_score(query, contact, match_type, context)
        
        print(scorer.explain_score(score))
        print("-" * 40)


if __name__ == '__main__':
    test_scoring()