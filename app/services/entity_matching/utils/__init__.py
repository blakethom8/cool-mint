"""Entity matching utilities package"""

from .scoring import MatchScorer, ScoringResult
from .text_utils import TextSimilarity, NameNormalizer, PhoneNormalizer
from .name_parser import NameParser, ParsedName

__all__ = [
    # Scoring
    'MatchScorer',
    'ScoringResult',
    
    # Text utilities
    'TextSimilarity',
    'NameNormalizer',
    'PhoneNormalizer',
    
    # Name parsing
    'NameParser',
    'ParsedName',
]