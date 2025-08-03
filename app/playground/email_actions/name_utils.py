"""Utilities for name parsing and normalization"""
import re
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass


@dataclass
class NameComponents:
    """Parsed name components"""
    first: Optional[str] = None
    middle: Optional[str] = None
    last: Optional[str] = None
    suffix: Optional[str] = None
    title: Optional[str] = None
    full_name: str = ""
    
    def to_dict(self) -> Dict:
        return {
            'first': self.first,
            'middle': self.middle,
            'last': self.last,
            'suffix': self.suffix,
            'title': self.title,
            'full_name': self.full_name
        }


class NameParser:
    """Parse and normalize names for matching"""
    
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
    
    def parse_name(self, full_name: str) -> NameComponents:
        """Parse a full name into components"""
        if not full_name:
            return NameComponents()
        
        original = full_name.strip()
        components = NameComponents(full_name=original)
        
        # Normalize whitespace
        name = ' '.join(full_name.split())
        
        # Extract titles (from beginning)
        name, titles = self._extract_titles(name)
        if titles:
            components.title = ', '.join(titles)
        
        # Extract suffixes (from end)
        name, suffixes = self._extract_suffixes(name)
        if suffixes:
            components.suffix = ', '.join(suffixes)
        
        # Split remaining name
        parts = name.split()
        
        if not parts:
            return components
        
        # Handle different name formats
        if len(parts) == 1:
            components.last = parts[0]
        elif len(parts) == 2:
            components.first = parts[0]
            components.last = parts[1]
        else:
            # 3 or more parts
            components.first = parts[0]
            
            # Check if last parts should be kept together (e.g., "Van Der Berg")
            last_parts = []
            i = len(parts) - 1
            
            # Work backwards to find compound last names
            while i > 0:
                if i > 1 and parts[i-1].lower() in self.prefixes:
                    last_parts.insert(0, parts[i-1])
                    i -= 1
                last_parts.insert(0, parts[i])
                break
            
            components.last = ' '.join(last_parts)
            
            # Everything else is middle
            if i > 1:
                components.middle = ' '.join(parts[1:i])
        
        return components
    
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
    
    def normalize_name(self, name: str) -> str:
        """Normalize name for comparison"""
        if not name:
            return ""
        
        # Remove extra whitespace
        name = ' '.join(name.split())
        
        # Remove punctuation except hyphens and apostrophes
        name = re.sub(r"[^\w\s\-']", " ", name)
        
        # Normalize whitespace again
        name = ' '.join(name.split())
        
        return name.strip()
    
    def extract_name_from_email(self, email: str) -> Optional[str]:
        """Extract likely name from email address"""
        if '@' not in email:
            return None
        
        local_part = email.split('@')[0]
        
        # Remove numbers at the end (e.g., john.smith2@)
        local_part = re.sub(r'\d+$', '', local_part)
        
        # Common separators
        for sep in ['.', '_', '-']:
            if sep in local_part:
                parts = local_part.split(sep)
                # Filter out common non-name parts
                parts = [p for p in parts if len(p) > 1 and not p.isdigit()]
                if parts:
                    return ' '.join(p.capitalize() for p in parts)
        
        # Single word - might be last name or username
        if local_part and len(local_part) > 2:
            return local_part.capitalize()
        
        return None
    
    def get_name_variations(self, name_components: NameComponents) -> List[str]:
        """Generate common variations of a name for matching"""
        variations = []
        
        # Full name as is
        if name_components.full_name:
            variations.append(name_components.full_name)
        
        # First Last
        if name_components.first and name_components.last:
            variations.append(f"{name_components.first} {name_components.last}")
        
        # Last, First
        if name_components.first and name_components.last:
            variations.append(f"{name_components.last}, {name_components.first}")
        
        # With middle initial
        if name_components.first and name_components.middle and name_components.last:
            middle_initial = name_components.middle[0]
            variations.append(f"{name_components.first} {middle_initial}. {name_components.last}")
            variations.append(f"{name_components.first} {middle_initial} {name_components.last}")
        
        # With title
        if name_components.title and name_components.last:
            variations.append(f"{name_components.title} {name_components.last}")
            if name_components.first:
                variations.append(f"{name_components.title} {name_components.first} {name_components.last}")
        
        # Nickname possibilities (common medical names)
        if name_components.first:
            nicknames = self._get_common_nicknames(name_components.first)
            for nickname in nicknames:
                if name_components.last:
                    variations.append(f"{nickname} {name_components.last}")
        
        return list(set(variations))  # Remove duplicates
    
    def _get_common_nicknames(self, first_name: str) -> List[str]:
        """Get common nicknames for a given first name"""
        nickname_map = {
            'william': ['will', 'bill'],
            'robert': ['rob', 'bob'],
            'richard': ['rick', 'dick'],
            'michael': ['mike'],
            'christopher': ['chris'],
            'jonathan': ['jon'],
            'joseph': ['joe'],
            'thomas': ['tom'],
            'charles': ['chuck', 'charlie'],
            'james': ['jim', 'jimmy'],
            'john': ['jack'],
            'elizabeth': ['liz', 'beth', 'betty'],
            'margaret': ['maggie', 'meg'],
            'jennifer': ['jen', 'jenny'],
            'patricia': ['pat', 'patty'],
            'susan': ['sue'],
            'deborah': ['deb', 'debbie'],
            'katherine': ['kate', 'kathy', 'katie'],
            'catherine': ['cathy', 'cat', 'kate']
        }
        
        first_lower = first_name.lower()
        return nickname_map.get(first_lower, [])


# Test the name parser
def test_name_parser():
    """Test name parsing functionality"""
    parser = NameParser()
    
    test_names = [
        "Dr. John Smith MD",
        "Sarah Johnson-Williams",
        "Michael Van Der Berg",
        "Dr. Maria Garcia Rodriguez Jr.",
        "John Michael Smith III",
        "O'Brien, Patrick",
        "MacDonald, Ronald MD",
        "St. James, Christopher",
        "john.smith@hospital.org",
        "sarah_johnson@clinic.com"
    ]
    
    print("Name Parser Test Results")
    print("=" * 60)
    
    for name in test_names:
        print(f"\nInput: '{name}'")
        
        if '@' in name:
            # Email extraction
            extracted = parser.extract_name_from_email(name)
            print(f"Extracted from email: {extracted}")
        else:
            # Name parsing
            parsed = parser.parse_name(name)
            print(f"Parsed components:")
            for key, value in parsed.to_dict().items():
                if value and key != 'full_name':
                    print(f"  {key}: {value}")
            
            # Variations
            variations = parser.get_name_variations(parsed)
            if variations:
                print(f"Variations: {variations[:3]}...")  # Show first 3


if __name__ == '__main__':
    test_name_parser()