"""Text processing and similarity utilities for entity matching"""
from difflib import SequenceMatcher
from typing import List, Set, Tuple
import re


class TextSimilarity:
    """String similarity calculation methods"""
    
    @staticmethod
    def ratio(str1: str, str2: str) -> float:
        """
        Calculate basic similarity ratio between two strings
        
        Args:
            str1: First string
            str2: Second string
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        if not str1 or not str2:
            return 0.0
        return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()
    
    @staticmethod
    def token_set_ratio(str1: str, str2: str) -> float:
        """
        Token set ratio - order doesn't matter
        
        Args:
            str1: First string
            str2: Second string
            
        Returns:
            Ratio of common tokens to total unique tokens
        """
        tokens1 = set(str1.lower().split())
        tokens2 = set(str2.lower().split())
        
        if not tokens1 or not tokens2:
            return 0.0
        
        intersection = tokens1 & tokens2
        union = tokens1 | tokens2
        
        return len(intersection) / len(union) if union else 0.0
    
    @staticmethod
    def partial_ratio(str1: str, str2: str) -> float:
        """
        Find best partial match between strings
        
        Args:
            str1: First string
            str2: Second string
            
        Returns:
            Best partial match score
        """
        if not str1 or not str2:
            return 0.0
        
        shorter = str1 if len(str1) <= len(str2) else str2
        longer = str2 if len(str1) <= len(str2) else str1
        
        matcher = SequenceMatcher(None, shorter.lower(), longer.lower())
        return matcher.ratio()
    
    @staticmethod
    def weighted_ratio(str1: str, str2: str) -> float:
        """
        Weighted combination of different similarity ratios
        
        Args:
            str1: First string
            str2: Second string
            
        Returns:
            Weighted average of different similarity metrics
        """
        # Simple ratio
        simple = TextSimilarity.ratio(str1, str2)
        
        # Token set ratio
        token_set = TextSimilarity.token_set_ratio(str1, str2)
        
        # Partial ratio
        partial = TextSimilarity.partial_ratio(str1, str2)
        
        # Weighted average
        return (simple * 0.5 + token_set * 0.3 + partial * 0.2)


class NameNormalizer:
    """Name normalization utilities"""
    
    # Common medical titles
    MEDICAL_TITLES = {
        'dr', 'dr.', 'doctor',
        'md', 'm.d.', 'do', 'd.o.',
        'phd', 'ph.d.', 'rn', 'r.n.',
        'np', 'n.p.', 'pa', 'p.a.',
        'dds', 'd.d.s.', 'dmd', 'd.m.d.',
        'pharmd', 'pharm.d.'
    }
    
    # Name suffixes
    NAME_SUFFIXES = {
        'jr', 'jr.', 'sr', 'sr.',
        'ii', 'iii', 'iv', 'v',
        'esq', 'esq.', 'phd', 'md'
    }
    
    @classmethod
    def remove_titles(cls, name: str) -> str:
        """
        Remove common medical titles from name
        
        Args:
            name: Name potentially containing titles
            
        Returns:
            Name with titles removed
        """
        if not name:
            return ""
        
        # Normalize for comparison
        name_lower = name.lower().replace('.', ' ')
        words = name_lower.split()
        
        # Filter out titles
        filtered_words = []
        for word in words:
            if word not in cls.MEDICAL_TITLES:
                filtered_words.append(word)
        
        # Reconstruct name preserving original capitalization
        if filtered_words:
            original_words = name.split()
            result_words = []
            
            for orig_word in original_words:
                if orig_word.lower().replace('.', '') not in cls.MEDICAL_TITLES:
                    result_words.append(orig_word)
            
            return ' '.join(result_words)
        
        return name
    
    @classmethod
    def normalize_name(cls, name: str) -> str:
        """
        Normalize name for comparison
        
        Args:
            name: Name to normalize
            
        Returns:
            Normalized name
        """
        if not name:
            return ""
        
        # Remove extra whitespace
        name = ' '.join(name.split())
        
        # Remove punctuation except hyphens and apostrophes
        name = re.sub(r"[^\w\s\-']", " ", name)
        
        # Normalize whitespace again
        name = ' '.join(name.split())
        
        return name.strip()
    
    @classmethod
    def extract_name_from_email(cls, email: str) -> str:
        """
        Extract likely name from email address
        
        Args:
            email: Email address
            
        Returns:
            Extracted name or empty string
        """
        if '@' not in email:
            return ""
        
        local_part = email.split('@')[0]
        
        # Remove numbers at the end
        local_part = re.sub(r'\d+$', '', local_part)
        
        # Replace common separators with spaces
        for sep in ['.', '_', '-']:
            local_part = local_part.replace(sep, ' ')
        
        # Filter out common non-name parts
        parts = [p for p in local_part.split() if len(p) > 1 and not p.isdigit()]
        
        if parts:
            # Capitalize each part
            return ' '.join(p.capitalize() for p in parts)
        
        return ""
    
    @classmethod
    def split_full_name(cls, full_name: str) -> Tuple[str, str, str]:
        """
        Split full name into first, middle, last components
        
        Args:
            full_name: Full name to split
            
        Returns:
            Tuple of (first_name, middle_name, last_name)
        """
        if not full_name:
            return "", "", ""
        
        # Remove titles first
        clean_name = cls.remove_titles(full_name)
        parts = clean_name.split()
        
        if not parts:
            return "", "", ""
        
        if len(parts) == 1:
            return "", "", parts[0]
        elif len(parts) == 2:
            return parts[0], "", parts[1]
        else:
            # 3 or more parts
            return parts[0], ' '.join(parts[1:-1]), parts[-1]


class PhoneNormalizer:
    """Phone number normalization utilities"""
    
    @staticmethod
    def normalize_phone(phone: str) -> str:
        """
        Normalize phone number to digits only
        
        Args:
            phone: Phone number in any format
            
        Returns:
            Normalized phone number (digits only)
        """
        if not phone:
            return ""
        
        # Remove all non-digit characters
        digits = re.sub(r'\D', '', phone)
        
        # Remove leading 1 for US numbers
        if len(digits) == 11 and digits.startswith('1'):
            digits = digits[1:]
        
        return digits
    
    @staticmethod
    def format_phone(phone: str) -> str:
        """
        Format phone number for display
        
        Args:
            phone: Normalized phone number
            
        Returns:
            Formatted phone number
        """
        digits = PhoneNormalizer.normalize_phone(phone)
        
        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        elif len(digits) == 7:
            return f"{digits[:3]}-{digits[3:]}"
        else:
            return phone