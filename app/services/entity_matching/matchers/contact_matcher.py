"""Contact entity matcher implementation"""
from typing import List, Optional, Dict
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..base import BaseEntityMatcher, MatcherRegistry
from ..models.match_results import (
    MatchResult, ContactMatch, MatchContext, 
    EntityType, MatchType
)
from ..utils.text_utils import TextSimilarity, NameNormalizer
from ..utils.name_parser import NameParser


class ContactMatcher(BaseEntityMatcher):
    """Matcher for contact entities"""
    
    def __init__(self, session: Optional[Session] = None):
        """Initialize contact matcher"""
        super().__init__(session)
        self.name_parser = NameParser()
        self.text_sim = TextSimilarity()
        self.name_norm = NameNormalizer()
    
    def match(self, query: str, context: Optional[MatchContext] = None) -> List[MatchResult]:
        """
        Match contacts based on query
        
        Args:
            query: Search query (email, name, NPI, etc.)
            context: Optional matching context
            
        Returns:
            List of ContactMatch results sorted by confidence
        """
        if not query or not query.strip():
            return []
        
        query = query.strip()
        matches = []
        
        # Try different matching strategies
        
        # 1. Email match (highest priority)
        if '@' in query:
            email_matches = self._match_by_email(query)
            matches.extend(email_matches)
        
        # 2. NPI match
        if query.isdigit() and len(query) == 10:
            npi_matches = self._match_by_npi(query)
            matches.extend(npi_matches)
        
        # 3. Name matching
        name_matches = self._match_by_name(query, context)
        matches.extend(name_matches)
        
        # Deduplicate and sort by confidence
        seen_ids = set()
        unique_matches = []
        for match in sorted(matches, key=lambda x: x.confidence_score, reverse=True):
            if match.entity_id not in seen_ids:
                seen_ids.add(match.entity_id)
                unique_matches.append(match)
        
        return unique_matches[:10]  # Return top 10
    
    def _match_by_email(self, email: str) -> List[ContactMatch]:
        """Exact email match"""
        result = self.session.execute(text("""
            SELECT id, salesforce_id, name, email, phone, specialty, 
                   contact_account_name, npi, active
            FROM sf_contacts
            WHERE LOWER(email) = LOWER(:email)
            LIMIT 5
        """), {"email": email})
        
        matches = []
        for row in result:
            matches.append(ContactMatch(
                entity_id=str(row.id),
                entity_type=EntityType.CONTACT,
                display_name=row.name or email,
                match_type=MatchType.EMAIL,
                confidence_score=1.0,
                match_details={"matched_email": email},
                active=row.active if row.active is not None else True,
                salesforce_id=row.salesforce_id,
                email=row.email,
                phone=row.phone,
                specialty=row.specialty,
                organization=row.contact_account_name,
                npi=row.npi
            ))
        
        return matches
    
    def _match_by_npi(self, npi: str) -> List[ContactMatch]:
        """Exact NPI match"""
        result = self.session.execute(text("""
            SELECT id, salesforce_id, name, email, phone, specialty, 
                   contact_account_name, npi, active
            FROM sf_contacts
            WHERE npi = :npi OR npi_mn = :npi
            LIMIT 5
        """), {"npi": npi})
        
        matches = []
        for row in result:
            matches.append(ContactMatch(
                entity_id=str(row.id),
                entity_type=EntityType.CONTACT,
                display_name=row.name or f"NPI: {npi}",
                match_type=MatchType.NPI,
                confidence_score=1.0,
                match_details={"matched_npi": npi},
                active=row.active if row.active is not None else True,
                salesforce_id=row.salesforce_id,
                email=row.email,
                phone=row.phone,
                specialty=row.specialty,
                organization=row.contact_account_name,
                npi=row.npi
            ))
        
        return matches
    
    def _match_by_name(self, name_query: str, 
                      context: Optional[MatchContext] = None) -> List[ContactMatch]:
        """Various name matching strategies"""
        matches = []
        
        # Parse and normalize the query
        cleaned_name = self.name_norm.remove_titles(name_query)
        parsed_name = self.name_parser.parse(name_query)
        name_parts = cleaned_name.lower().split()
        
        if not name_parts:
            return matches
        
        # 1. Exact full name match
        matches.extend(self._exact_name_match(cleaned_name))
        
        # 2. Last name match (if single word)
        if len(name_parts) == 1:
            matches.extend(self._last_name_match(name_parts[0], context))
        
        # 3. First + Last name match
        elif len(name_parts) >= 2:
            first_name = name_parts[0]
            last_name = name_parts[-1]
            matches.extend(self._first_last_match(first_name, last_name))
        
        # 4. Fuzzy name matching
        if len(matches) < 5:
            fuzzy_matches = self._fuzzy_name_match(cleaned_name, matches)
            matches.extend(fuzzy_matches)
        
        return matches
    
    def _exact_name_match(self, name: str) -> List[ContactMatch]:
        """Exact name matching"""
        result = self.session.execute(text("""
            SELECT id, salesforce_id, name, email, phone, specialty, 
                   contact_account_name, npi, active
            FROM sf_contacts
            WHERE LOWER(name) = LOWER(:name)
            LIMIT 5
        """), {"name": name})
        
        matches = []
        for row in result:
            confidence = 0.95
            if not row.active:
                confidence *= 0.8
            
            matches.append(ContactMatch(
                entity_id=str(row.id),
                entity_type=EntityType.CONTACT,
                display_name=row.name,
                match_type=MatchType.EXACT_NAME,
                confidence_score=confidence,
                match_details={"matched_name": name},
                active=row.active if row.active is not None else True,
                salesforce_id=row.salesforce_id,
                email=row.email,
                phone=row.phone,
                specialty=row.specialty,
                organization=row.contact_account_name,
                npi=row.npi
            ))
        
        return matches
    
    def _last_name_match(self, last_name: str, 
                        context: Optional[MatchContext] = None) -> List[ContactMatch]:
        """Last name only matching"""
        result = self.session.execute(text("""
            SELECT id, salesforce_id, name, first_name, last_name, 
                   email, phone, specialty, contact_account_name, npi, active
            FROM sf_contacts
            WHERE LOWER(last_name) = :last_name
            LIMIT 20
        """), {"last_name": last_name})
        
        matches = []
        for row in result:
            confidence = 0.7
            
            # Boost confidence based on context
            if context:
                if context.organization and row.contact_account_name:
                    if context.organization.lower() in row.contact_account_name.lower():
                        confidence = 0.85
                
                if context.specialty and row.specialty:
                    if context.specialty.lower() in row.specialty.lower():
                        confidence += 0.1
            
            if not row.active:
                confidence *= 0.8
            
            matches.append(ContactMatch(
                entity_id=str(row.id),
                entity_type=EntityType.CONTACT,
                display_name=row.name,
                match_type=MatchType.LAST_NAME,
                confidence_score=confidence,
                match_details={
                    "matched_last_name": last_name,
                    "full_name": row.name
                },
                active=row.active if row.active is not None else True,
                salesforce_id=row.salesforce_id,
                email=row.email,
                phone=row.phone,
                specialty=row.specialty,
                organization=row.contact_account_name,
                npi=row.npi
            ))
        
        return matches
    
    def _first_last_match(self, first_name: str, last_name: str) -> List[ContactMatch]:
        """First and last name matching"""
        result = self.session.execute(text("""
            SELECT id, salesforce_id, name, email, phone, specialty, 
                   contact_account_name, npi, active
            FROM sf_contacts
            WHERE LOWER(first_name) = :first_name 
            AND LOWER(last_name) = :last_name
            LIMIT 10
        """), {"first_name": first_name, "last_name": last_name})
        
        matches = []
        for row in result:
            confidence = 0.9
            if not row.active:
                confidence *= 0.8
            
            matches.append(ContactMatch(
                entity_id=str(row.id),
                entity_type=EntityType.CONTACT,
                display_name=row.name,
                match_type=MatchType.FIRST_LAST_NAME,
                confidence_score=confidence,
                match_details={
                    "matched_first": first_name,
                    "matched_last": last_name
                },
                active=row.active if row.active is not None else True,
                salesforce_id=row.salesforce_id,
                email=row.email,
                phone=row.phone,
                specialty=row.specialty,
                organization=row.contact_account_name,
                npi=row.npi
            ))
        
        return matches
    
    def _fuzzy_name_match(self, name: str, 
                         existing_matches: List[ContactMatch]) -> List[ContactMatch]:
        """Fuzzy name matching"""
        pattern = f"%{name}%"
        
        # Build exclude clause if we have matches
        exclude_ids = [m.entity_id for m in existing_matches]
        if exclude_ids:
            exclude_clause = "AND id NOT IN (" + ",".join([f"'{id}'" for id in exclude_ids]) + ")"
        else:
            exclude_clause = ""
        
        result = self.session.execute(text(f"""
            SELECT id, salesforce_id, name, email, phone, specialty, 
                   contact_account_name, npi, active
            FROM sf_contacts
            WHERE LOWER(name) LIKE LOWER(:pattern)
            {exclude_clause}
            LIMIT 10
        """), {"pattern": pattern})
        
        matches = []
        for row in result:
            # Calculate similarity
            similarity = self.text_sim.ratio(name, row.name)
            confidence = similarity * 0.8
            
            if not row.active:
                confidence *= 0.8
            
            if confidence > 0.5:  # Threshold
                matches.append(ContactMatch(
                    entity_id=str(row.id),
                    entity_type=EntityType.CONTACT,
                    display_name=row.name,
                    match_type=MatchType.FUZZY_NAME,
                    confidence_score=confidence,
                    match_details={
                        "query": name,
                        "matched_name": row.name,
                        "similarity": round(similarity, 3)
                    },
                    active=row.active if row.active is not None else True,
                    salesforce_id=row.salesforce_id,
                    email=row.email,
                    phone=row.phone,
                    specialty=row.specialty,
                    organization=row.contact_account_name,
                    npi=row.npi
                ))
        
        return matches


# Register the matcher
MatcherRegistry.register(EntityType.CONTACT, ContactMatcher)