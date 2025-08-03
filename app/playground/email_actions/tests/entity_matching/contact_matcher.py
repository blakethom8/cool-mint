#!/usr/bin/env python3
"""Contact matching service for resolving names to database records"""
import re
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass
from difflib import SequenceMatcher
from sqlalchemy import or_, func, and_
from sqlalchemy.orm import Session

# Add parent directories to path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[2]))

from database.session import db_session
from database.data_models.salesforce_data import SfContact


@dataclass
class ContactMatch:
    """Represents a potential contact match with confidence scoring"""
    contact: SfContact
    match_type: str  # "email", "name", "npi", "fuzzy_name", etc.
    confidence_score: float  # 0.0 to 1.0
    match_details: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for easy display"""
        return {
            'id': str(self.contact.id),
            'salesforce_id': self.contact.salesforce_id,
            'name': self.contact.name,
            'email': self.contact.email,
            'specialty': self.contact.specialty,
            'match_type': self.match_type,
            'confidence': round(self.confidence_score, 3),
            'details': self.match_details
        }


class ContactMatcher:
    """Service for matching natural language queries to contacts"""
    
    def __init__(self, session: Optional[Session] = None):
        self.session = session
        # Common medical titles to remove for matching
        self.titles = {
            'dr', 'dr.', 'doctor', 
            'md', 'm.d.', 'do', 'd.o.',
            'phd', 'ph.d.', 'rn', 'r.n.',
            'np', 'n.p.', 'pa', 'p.a.'
        }
        
    def match_contact(self, query: str, context: Optional[Dict] = None) -> List[ContactMatch]:
        """
        Main entry point for contact matching
        
        Args:
            query: Search string (email, name, etc.)
            context: Optional context like organization, specialty
            
        Returns:
            List of ContactMatch objects sorted by confidence
        """
        if not query or not query.strip():
            return []
            
        query = query.strip()
        matches = []
        
        for session in db_session() if not self.session else [self.session]:
            # Try different matching strategies
            
            # 1. Email match (highest priority)
            if '@' in query:
                email_match = self._match_by_email(session, query)
                if email_match:
                    matches.append(email_match)
            
            # 2. NPI match
            if query.isdigit() and len(query) == 10:
                npi_match = self._match_by_npi(session, query)
                if npi_match:
                    matches.append(npi_match)
            
            # 3. External ID match
            external_match = self._match_by_external_id(session, query)
            if external_match:
                matches.append(external_match)
            
            # 4. Name matching (various strategies)
            name_matches = self._match_by_name(session, query, context)
            matches.extend(name_matches)
            
            # Only process first session if using db_session()
            if not self.session:
                break
        
        # Deduplicate and sort by confidence
        seen_ids = set()
        unique_matches = []
        for match in sorted(matches, key=lambda x: x.confidence_score, reverse=True):
            if match.contact.id not in seen_ids:
                seen_ids.add(match.contact.id)
                unique_matches.append(match)
        
        return unique_matches
    
    def _match_by_email(self, session: Session, email: str) -> Optional[ContactMatch]:
        """Exact email match"""
        contact = session.query(SfContact).filter(
            func.lower(SfContact.email) == email.lower()
        ).first()
        
        if contact:
            return ContactMatch(
                contact=contact,
                match_type="email",
                confidence_score=1.0,
                match_details={"matched_email": email}
            )
        return None
    
    def _match_by_npi(self, session: Session, npi: str) -> Optional[ContactMatch]:
        """Exact NPI match"""
        contact = session.query(SfContact).filter(
            or_(SfContact.npi == npi, SfContact.npi_mn == npi)
        ).first()
        
        if contact:
            return ContactMatch(
                contact=contact,
                match_type="npi",
                confidence_score=1.0,
                match_details={"matched_npi": npi}
            )
        return None
    
    def _match_by_external_id(self, session: Session, external_id: str) -> Optional[ContactMatch]:
        """Exact external ID match"""
        contact = session.query(SfContact).filter(
            SfContact.external_id == external_id
        ).first()
        
        if contact:
            return ContactMatch(
                contact=contact,
                match_type="external_id",
                confidence_score=1.0,
                match_details={"matched_external_id": external_id}
            )
        return None
    
    def _match_by_name(self, session: Session, name_query: str, 
                      context: Optional[Dict] = None) -> List[ContactMatch]:
        """Various name matching strategies"""
        matches = []
        
        # Parse and normalize the query
        cleaned_name = self._remove_titles(name_query)
        name_parts = cleaned_name.lower().split()
        
        if not name_parts:
            return matches
        
        # 1. Exact full name match
        exact_matches = session.query(SfContact).filter(
            func.lower(SfContact.name) == cleaned_name.lower()
        ).all()
        
        for contact in exact_matches:
            matches.append(ContactMatch(
                contact=contact,
                match_type="exact_name",
                confidence_score=0.95,
                match_details={"matched_name": cleaned_name}
            ))
        
        # 2. Last name match (if we likely have just last name)
        if len(name_parts) == 1:
            last_name = name_parts[0]
            last_name_matches = session.query(SfContact).filter(
                func.lower(SfContact.last_name) == last_name
            ).all()
            
            for contact in last_name_matches:
                confidence = 0.7
                # Boost confidence if context matches
                if context and context.get('organization'):
                    if contact.contact_account_name and \
                       context['organization'].lower() in contact.contact_account_name.lower():
                        confidence = 0.85
                
                matches.append(ContactMatch(
                    contact=contact,
                    match_type="last_name",
                    confidence_score=confidence,
                    match_details={
                        "matched_last_name": last_name,
                        "full_name": contact.name
                    }
                ))
        
        # 3. First + Last name match
        elif len(name_parts) >= 2:
            # Try different combinations
            first_name = name_parts[0]
            last_name = name_parts[-1]
            
            # Exact first + last
            name_matches = session.query(SfContact).filter(
                and_(
                    func.lower(SfContact.first_name) == first_name,
                    func.lower(SfContact.last_name) == last_name
                )
            ).all()
            
            for contact in name_matches:
                matches.append(ContactMatch(
                    contact=contact,
                    match_type="first_last_name",
                    confidence_score=0.9,
                    match_details={
                        "matched_first": first_name,
                        "matched_last": last_name
                    }
                ))
        
        # 4. Fuzzy name matching for remaining candidates
        if len(matches) < 5:  # Only if we don't have many exact matches
            fuzzy_matches = self._fuzzy_name_match(session, cleaned_name, name_parts)
            matches.extend(fuzzy_matches)
        
        return matches
    
    def _fuzzy_name_match(self, session: Session, cleaned_name: str, 
                         name_parts: List[str]) -> List[ContactMatch]:
        """Fuzzy string matching for names"""
        matches = []
        
        # Get candidates based on partial matches
        conditions = []
        for part in name_parts:
            if len(part) > 2:  # Skip very short parts
                conditions.extend([
                    func.lower(SfContact.first_name).contains(part),
                    func.lower(SfContact.last_name).contains(part),
                    func.lower(SfContact.name).contains(part)
                ])
        
        if not conditions:
            return matches
        
        candidates = session.query(SfContact).filter(
            or_(*conditions)
        ).limit(50).all()
        
        # Score each candidate
        for contact in candidates:
            if contact.name:
                # Calculate similarity score
                contact_name_clean = self._remove_titles(contact.name)
                similarity = SequenceMatcher(None, 
                                           cleaned_name.lower(), 
                                           contact_name_clean.lower()).ratio()
                
                if similarity > 0.6:  # Threshold for fuzzy matches
                    matches.append(ContactMatch(
                        contact=contact,
                        match_type="fuzzy_name",
                        confidence_score=similarity * 0.8,  # Scale down fuzzy matches
                        match_details={
                            "query": cleaned_name,
                            "matched_name": contact.name,
                            "similarity": round(similarity, 3)
                        }
                    ))
        
        return matches
    
    def _remove_titles(self, name: str) -> str:
        """Remove common medical titles from name"""
        # Remove periods and convert to lowercase for comparison
        name_lower = name.lower().replace('.', ' ')
        
        # Split into words
        words = name_lower.split()
        
        # Filter out titles
        filtered_words = []
        for word in words:
            if word not in self.titles:
                filtered_words.append(word)
        
        # Reconstruct name, preserving original case where possible
        if filtered_words:
            # Try to maintain original capitalization
            original_words = name.split()
            result_words = []
            
            j = 0
            for i, orig_word in enumerate(original_words):
                if orig_word.lower().replace('.', '') not in self.titles:
                    result_words.append(orig_word)
                    j += 1
            
            return ' '.join(result_words)
        
        return name
    
    def extract_name_from_email(self, email: str) -> Optional[str]:
        """Extract potential name from email address"""
        if '@' not in email:
            return None
        
        local_part = email.split('@')[0]
        
        # Common patterns
        # john.smith@example.com -> John Smith
        # jsmith@example.com -> J Smith
        # john_smith@example.com -> John Smith
        
        # Replace common separators with spaces
        name = local_part.replace('.', ' ').replace('_', ' ').replace('-', ' ')
        
        # Capitalize words
        name_parts = name.split()
        capitalized = [part.capitalize() for part in name_parts if part]
        
        return ' '.join(capitalized) if capitalized else None


# Utility function for testing
def test_matcher():
    """Test the contact matcher with various inputs"""
    matcher = ContactMatcher()
    
    test_queries = [
        "dr.destefano@example.com",
        "Dr. DeStefano",
        "DeStefano",
        "Sarah Johnson",
        "Dr. Sarah Johnson from Cedars",
        "1234567890",  # NPI example
    ]
    
    print("Contact Matcher Test Results")
    print("=" * 60)
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        print("-" * 40)
        
        # Extract context if present
        context = None
        if "from" in query.lower():
            parts = query.lower().split("from")
            if len(parts) > 1:
                context = {"organization": parts[1].strip()}
                query = parts[0].strip()
        
        matches = matcher.match_contact(query, context)
        
        if matches:
            print(f"Found {len(matches)} match(es):")
            for i, match in enumerate(matches[:5]):  # Show top 5
                result = match.to_dict()
                print(f"\n  {i+1}. {result['name']} ({result['match_type']})")
                print(f"     Email: {result['email']}")
                print(f"     Specialty: {result['specialty']}")
                print(f"     Confidence: {result['confidence']}")
                print(f"     Details: {result['details']}")
        else:
            print("No matches found")


if __name__ == '__main__':
    test_matcher()