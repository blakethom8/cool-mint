"""Name parsing utilities for entity matching"""
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass
import re


@dataclass
class ParsedName:
    """Parsed name components"""
    first: Optional[str] = None
    middle: Optional[str] = None
    last: Optional[str] = None
    suffix: Optional[str] = None
    title: Optional[str] = None
    full_name: str = ""
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'first': self.first,
            'middle': self.middle,
            'last': self.last,
            'suffix': self.suffix,
            'title': self.title,
            'full_name': self.full_name
        }
    
    def get_display_name(self) -> str:
        """Get formatted display name"""
        parts = []
        if self.title:
            parts.append(self.title)
        if self.first:
            parts.append(self.first)
        if self.middle:
            parts.append(self.middle)
        if self.last:
            parts.append(self.last)
        if self.suffix:
            parts.append(self.suffix)
        return ' '.join(parts)


class NameParser:
    """Advanced name parsing functionality"""
    
    def __init__(self):
        # Medical titles
        self.titles = {
            'dr', 'dr.', 'doctor',
            'md', 'm.d.', 'do', 'd.o.',
            'phd', 'ph.d.', 'rn', 'r.n.',
            'np', 'n.p.', 'pa', 'p.a.',
            'dds', 'd.d.s.', 'dmd', 'd.m.d.',
            'pharmd', 'pharm.d.'
        }
        
        # Name suffixes
        self.suffixes = {
            'jr', 'jr.', 'sr', 'sr.',
            'ii', 'iii', 'iv', 'v',
            'esq', 'esq.', 'phd', 'md'
        }
        
        # Common name prefixes (keep with name)
        self.prefixes = {
            'de', 'del', 'della', 'di', 'da',
            'van', 'von', 'der', 'den',
            'la', 'le', 'los', 'las',
            'mac', 'mc', "o'", 'st', 'st.'
        }
        
        # Common nicknames mapping
        self.nicknames = {
            'william': ['will', 'bill', 'billy'],
            'robert': ['rob', 'bob', 'bobby'],
            'richard': ['rick', 'dick', 'rich'],
            'michael': ['mike', 'mick', 'mickey'],
            'christopher': ['chris', 'kit'],
            'jonathan': ['jon', 'john'],
            'joseph': ['joe', 'joey'],
            'thomas': ['tom', 'tommy'],
            'charles': ['chuck', 'charlie', 'chas'],
            'james': ['jim', 'jimmy', 'jamie'],
            'john': ['jack', 'johnny'],
            'david': ['dave', 'davey'],
            'daniel': ['dan', 'danny'],
            'matthew': ['matt', 'matty'],
            'andrew': ['andy', 'drew'],
            'elizabeth': ['liz', 'beth', 'betty', 'eliza', 'libby'],
            'margaret': ['maggie', 'meg', 'peggy', 'marge'],
            'jennifer': ['jen', 'jenny'],
            'patricia': ['pat', 'patty', 'trish'],
            'susan': ['sue', 'suzy'],
            'deborah': ['deb', 'debbie', 'debby'],
            'katherine': ['kate', 'kathy', 'katie', 'kat'],
            'catherine': ['cathy', 'cat', 'kate', 'katie']
        }
    
    def parse(self, full_name: str) -> ParsedName:
        """
        Parse a full name into components
        
        Args:
            full_name: Full name to parse
            
        Returns:
            ParsedName object with components
        """
        if not full_name:
            return ParsedName()
        
        original = full_name.strip()
        parsed = ParsedName(full_name=original)
        
        # Normalize whitespace
        name = ' '.join(full_name.split())
        
        # Extract titles (from beginning)
        name, titles = self._extract_titles(name)
        if titles:
            parsed.title = ', '.join(titles)
        
        # Extract suffixes (from end)
        name, suffixes = self._extract_suffixes(name)
        if suffixes:
            parsed.suffix = ', '.join(suffixes)
        
        # Split remaining name
        parts = name.split()
        
        if not parts:
            return parsed
        
        # Handle different name formats
        if len(parts) == 1:
            parsed.last = parts[0]
        elif len(parts) == 2:
            parsed.first = parts[0]
            parsed.last = parts[1]
        else:
            # 3 or more parts - handle compound last names
            parsed.first = parts[0]
            
            # Check if last parts should be kept together
            last_parts = []
            i = len(parts) - 1
            
            # Work backwards to find compound last names
            while i > 0:
                if i > 1 and parts[i-1].lower() in self.prefixes:
                    last_parts.insert(0, parts[i-1])
                    i -= 1
                last_parts.insert(0, parts[i])
                break
            
            parsed.last = ' '.join(last_parts)
            
            # Everything else is middle
            if i > 1:
                parsed.middle = ' '.join(parts[1:i])
        
        return parsed
    
    def _extract_titles(self, name: str) -> Tuple[str, List[str]]:
        """Extract titles from the beginning of name"""
        titles = []
        parts = name.split()
        
        i = 0
        while i < len(parts) and parts[i].lower().rstrip('.') in self.titles:
            titles.append(parts[i])
            i += 1
        
        remaining = ' '.join(parts[i:])
        return remaining, titles
    
    def _extract_suffixes(self, name: str) -> Tuple[str, List[str]]:
        """Extract suffixes from the end of name"""
        suffixes = []
        parts = name.split()
        
        while parts and parts[-1].lower().rstrip('.') in self.suffixes:
            suffixes.insert(0, parts.pop())
        
        remaining = ' '.join(parts)
        return remaining, suffixes
    
    def get_name_variations(self, parsed_name: ParsedName) -> List[str]:
        """
        Generate common variations of a name for matching
        
        Args:
            parsed_name: ParsedName object
            
        Returns:
            List of name variations
        """
        variations = []
        
        # Full name as is
        if parsed_name.full_name:
            variations.append(parsed_name.full_name)
        
        # First Last
        if parsed_name.first and parsed_name.last:
            variations.append(f"{parsed_name.first} {parsed_name.last}")
        
        # Last, First
        if parsed_name.first and parsed_name.last:
            variations.append(f"{parsed_name.last}, {parsed_name.first}")
        
        # With middle initial
        if parsed_name.first and parsed_name.middle and parsed_name.last:
            middle_initial = parsed_name.middle[0]
            variations.append(f"{parsed_name.first} {middle_initial}. {parsed_name.last}")
            variations.append(f"{parsed_name.first} {middle_initial} {parsed_name.last}")
        
        # With title
        if parsed_name.title and parsed_name.last:
            variations.append(f"{parsed_name.title} {parsed_name.last}")
            if parsed_name.first:
                variations.append(f"{parsed_name.title} {parsed_name.first} {parsed_name.last}")
        
        # Nickname variations
        if parsed_name.first:
            nicknames = self.get_nicknames(parsed_name.first)
            for nickname in nicknames:
                if parsed_name.last:
                    variations.append(f"{nickname} {parsed_name.last}")
        
        return list(set(variations))  # Remove duplicates
    
    def get_nicknames(self, first_name: str) -> List[str]:
        """
        Get common nicknames for a given first name
        
        Args:
            first_name: First name to find nicknames for
            
        Returns:
            List of possible nicknames
        """
        first_lower = first_name.lower()
        
        # Check if this name is a nickname itself
        reverse_nicknames = []
        for full_name, nicks in self.nicknames.items():
            if first_lower in nicks:
                reverse_nicknames.append(full_name.capitalize())
        
        # Get nicknames for this name
        direct_nicknames = [n.capitalize() for n in self.nicknames.get(first_lower, [])]
        
        return reverse_nicknames + direct_nicknames