#!/usr/bin/env python3
"""Contact matching service v2 - using direct SQL to avoid ORM issues"""

import re
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from difflib import SequenceMatcher
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Add parent directories to path
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))

load_dotenv()

# Database connection
DATABASE_HOST = os.getenv("DATABASE_HOST", "localhost")
DATABASE_NAME = os.getenv("DATABASE_NAME", "postgres")
DATABASE_USER = os.getenv("DATABASE_USER", "postgres")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
DATABASE_PORT = os.getenv("DATABASE_PORT", "5433")

DATABASE_URL = f"postgresql://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)


@dataclass
class ContactMatch:
    """Represents a potential contact match with confidence scoring"""

    id: str
    salesforce_id: str
    name: str
    email: Optional[str]
    specialty: Optional[str]
    organization: Optional[str]
    match_type: str
    confidence_score: float
    match_details: Dict[str, Any]

    def to_dict(self) -> Dict:
        """Convert to dictionary for easy display"""
        return {
            "id": self.id,
            "salesforce_id": self.salesforce_id,
            "name": self.name,
            "email": self.email,
            "specialty": self.specialty,
            "organization": self.organization,
            "match_type": self.match_type,
            "confidence": round(self.confidence_score, 3),
            "details": self.match_details,
        }


class ContactMatcherV2:
    """Service for matching natural language queries to contacts using SQL"""

    def __init__(self):
        self.session = Session()
        # Common medical titles to remove for matching
        self.titles = {
            "dr",
            "dr.",
            "doctor",
            "md",
            "m.d.",
            "do",
            "d.o.",
            "phd",
            "ph.d.",
            "rn",
            "r.n.",
            "np",
            "n.p.",
            "pa",
            "p.a.",
        }

    def match_contact(
        self, query: str, context: Optional[Dict] = None
    ) -> List[ContactMatch]:
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

        # Try different matching strategies

        # 1. Email match (highest priority)
        if "@" in query:
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
            if match.id not in seen_ids:
                seen_ids.add(match.id)
                unique_matches.append(match)

        return unique_matches[:10]  # Return top 10

    def _match_by_email(self, email: str) -> List[ContactMatch]:
        """Exact email match"""
        result = self.session.execute(
            text("""
            SELECT id, salesforce_id, name, email, specialty, 
                   contact_account_name, active
            FROM sf_contacts
            WHERE LOWER(email) = LOWER(:email)
            LIMIT 5
        """),
            {"email": email},
        )

        matches = []
        for row in result:
            matches.append(
                ContactMatch(
                    id=str(row.id),
                    salesforce_id=row.salesforce_id,
                    name=row.name,
                    email=row.email,
                    specialty=row.specialty,
                    organization=row.contact_account_name,
                    match_type="email",
                    confidence_score=1.0,
                    match_details={"matched_email": email},
                )
            )

        return matches

    def _match_by_npi(self, npi: str) -> List[ContactMatch]:
        """Exact NPI match"""
        result = self.session.execute(
            text("""
            SELECT id, salesforce_id, name, email, specialty, 
                   contact_account_name, active
            FROM sf_contacts
            WHERE npi = :npi OR npi_mn = :npi
            LIMIT 5
        """),
            {"npi": npi},
        )

        matches = []
        for row in result:
            matches.append(
                ContactMatch(
                    id=str(row.id),
                    salesforce_id=row.salesforce_id,
                    name=row.name,
                    email=row.email,
                    specialty=row.specialty,
                    organization=row.contact_account_name,
                    match_type="npi",
                    confidence_score=1.0,
                    match_details={"matched_npi": npi},
                )
            )

        return matches

    def _match_by_name(
        self, name_query: str, context: Optional[Dict] = None
    ) -> List[ContactMatch]:
        """Various name matching strategies"""
        matches = []

        # Parse and normalize the query
        cleaned_name = self._remove_titles(name_query)
        name_parts = cleaned_name.lower().split()

        if not name_parts:
            return matches

        # 1. Exact full name match
        result = self.session.execute(
            text("""
            SELECT id, salesforce_id, name, email, specialty, 
                   contact_account_name, active
            FROM sf_contacts
            WHERE LOWER(name) = LOWER(:name)
            LIMIT 5
        """),
            {"name": cleaned_name},
        )

        for row in result:
            confidence = 0.95
            if not row.active:
                confidence *= 0.8

            matches.append(
                ContactMatch(
                    id=str(row.id),
                    salesforce_id=row.salesforce_id,
                    name=row.name,
                    email=row.email,
                    specialty=row.specialty,
                    organization=row.contact_account_name,
                    match_type="exact_name",
                    confidence_score=confidence,
                    match_details={"matched_name": cleaned_name},
                )
            )

        # 2. Last name match (if we likely have just last name)
        if len(name_parts) == 1:
            last_name = name_parts[0]
            result = self.session.execute(
                text("""
                SELECT id, salesforce_id, name, first_name, last_name, 
                       email, specialty, contact_account_name, active
                FROM sf_contacts
                WHERE LOWER(last_name) = :last_name
                LIMIT 20
            """),
                {"last_name": last_name},
            )

            for row in result:
                confidence = 0.7

                # Boost confidence based on context
                if context:
                    if context.get("organization") and row.contact_account_name:
                        if (
                            context["organization"].lower()
                            in row.contact_account_name.lower()
                        ):
                            confidence = 0.85

                    if context.get("specialty") and row.specialty:
                        if context["specialty"].lower() in row.specialty.lower():
                            confidence += 0.1

                if not row.active:
                    confidence *= 0.8

                matches.append(
                    ContactMatch(
                        id=str(row.id),
                        salesforce_id=row.salesforce_id,
                        name=row.name,
                        email=row.email,
                        specialty=row.specialty,
                        organization=row.contact_account_name,
                        match_type="last_name",
                        confidence_score=confidence,
                        match_details={
                            "matched_last_name": last_name,
                            "full_name": row.name,
                        },
                    )
                )

        # 3. First + Last name match
        elif len(name_parts) >= 2:
            first_name = name_parts[0]
            last_name = name_parts[-1]

            # Try exact first + last
            result = self.session.execute(
                text("""
                SELECT id, salesforce_id, name, email, specialty, 
                       contact_account_name, active
                FROM sf_contacts
                WHERE LOWER(first_name) = :first_name 
                AND LOWER(last_name) = :last_name
                LIMIT 10
            """),
                {"first_name": first_name, "last_name": last_name},
            )

            for row in result:
                confidence = 0.9
                if not row.active:
                    confidence *= 0.8

                matches.append(
                    ContactMatch(
                        id=str(row.id),
                        salesforce_id=row.salesforce_id,
                        name=row.name,
                        email=row.email,
                        specialty=row.specialty,
                        organization=row.contact_account_name,
                        match_type="first_last_name",
                        confidence_score=confidence,
                        match_details={
                            "matched_first": first_name,
                            "matched_last": last_name,
                        },
                    )
                )

        # 4. Fuzzy name matching (LIKE queries)
        if len(matches) < 5:
            pattern = f"%{cleaned_name}%"

            # Build exclude clause if we have matches
            if matches:
                exclude_ids = [m.id for m in matches]
                exclude_clause = (
                    "AND id NOT IN ("
                    + ",".join([f"'{id}'" for id in exclude_ids])
                    + ")"
                )
            else:
                exclude_clause = ""

            result = self.session.execute(
                text(f"""
                SELECT id, salesforce_id, name, email, specialty, 
                       contact_account_name, active
                FROM sf_contacts
                WHERE LOWER(name) LIKE LOWER(:pattern)
                {exclude_clause}
                LIMIT 10
            """),
                {"pattern": pattern},
            )

            for row in result:
                # Calculate similarity
                similarity = self._calculate_similarity(
                    cleaned_name.lower(), row.name.lower()
                )
                confidence = similarity * 0.8

                if not row.active:
                    confidence *= 0.8

                if confidence > 0.5:  # Threshold
                    matches.append(
                        ContactMatch(
                            id=str(row.id),
                            salesforce_id=row.salesforce_id,
                            name=row.name,
                            email=row.email,
                            specialty=row.specialty,
                            organization=row.contact_account_name,
                            match_type="fuzzy_name",
                            confidence_score=confidence,
                            match_details={
                                "query": cleaned_name,
                                "matched_name": row.name,
                                "similarity": round(similarity, 3),
                            },
                        )
                    )

        return matches

    def _remove_titles(self, name: str) -> str:
        """Remove common medical titles from name"""
        name_lower = name.lower().replace(".", " ")
        words = name_lower.split()

        # Filter out titles
        filtered_words = []
        for word in words:
            if word not in self.titles:
                filtered_words.append(word)

        # Reconstruct name
        if filtered_words:
            # Try to maintain original capitalization
            original_words = name.split()
            result_words = []

            for orig_word in original_words:
                if orig_word.lower().replace(".", "") not in self.titles:
                    result_words.append(orig_word)

            return " ".join(result_words)

        return name

    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate string similarity"""
        return SequenceMatcher(None, str1, str2).ratio()

    def close(self):
        """Close database session"""
        self.session.close()


def test_matcher():
    """Test the contact matcher with various inputs"""
    matcher = ContactMatcherV2()

    test_queries = [
        ("uquillas", None),
        ("Dr. Uquillas", None),
        ("Carlos Guanche", None),
        ("Lauren Destefano", None),
        ("Dr. DeStefano", {"organization": "Cedars"}),
        ("boyd", {"specialty": "urology"}),
        ("monanyan@facey.com", None),
        ("Dr. Sharma", None),
        ("Dr. Shen", {"specialty": "Oncology"}),
    ]

    print("Contact Matcher V2 Test Results")
    print("=" * 80)

    try:
        for query, context in test_queries:
            print(f"\nQuery: '{query}'")
            if context:
                print(f"Context: {context}")
            print("-" * 60)

            matches = matcher.match_contact(query, context)

            if matches:
                print(f"Found {len(matches)} match(es):")
                for i, match in enumerate(matches[:5], 1):
                    result = match.to_dict()
                    print(f"\n  {i}. {result['name']} ({result['match_type']})")
                    print(f"     Email: {result['email'] or 'N/A'}")
                    print(f"     Specialty: {result['specialty'] or 'N/A'}")
                    print(f"     Organization: {result['organization'] or 'N/A'}")
                    print(f"     Confidence: {result['confidence']}")
                    if result["details"]:
                        print(f"     Details: {result['details']}")
            else:
                print("No matches found")
    finally:
        matcher.close()


if __name__ == "__main__":
    test_matcher()
