#!/usr/bin/env python3
"""Test script for the new entity matching service"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment
load_dotenv()

from services.entity_matching import EntityMatchingService, EntityType, MatchContext


def test_contact_matching():
    """Test contact matching functionality"""
    print("=" * 60)
    print("Testing Contact Matching")
    print("=" * 60)

    # Initialize service
    service = EntityMatchingService()

    # Test cases
    test_queries = [
        # Email matching
        {"query": "john.smith@example.com", "description": "Email match"},
        # Name matching
        {"query": "Dr. DeStefano", "description": "Name with title"},
        # Last name only
        {"query": "Smith", "description": "Last name only"},
        # NPI matching
        {"query": "1234567890", "description": "NPI match (if exists)"},
        # Name with context
        {
            "query": "Smith",
            "context": {"organization": "Cardiology Associates"},
            "description": "Last name with organization context",
        },
    ]

    for test in test_queries:
        print(f"\n{test['description']}: '{test['query']}'")
        print("-" * 40)

        context = test.get("context")
        if context:
            print(f"Context: {context}")

        # Use convenience method
        matches = service.match_contact(
            test["query"], context=context, with_scoring=True
        )

        if matches:
            for i, match in enumerate(matches[:3], 1):
                print(f"\n{i}. {match.display_name}")
                print(f"   ID: {match.salesforce_id}")
                print(f"   Email: {match.email}")
                print(f"   Organization: {match.organization}")
                print(f"   Specialty: {match.specialty}")
                print(f"   Match Type: {match.match_type.value}")
                print(f"   Confidence: {match.confidence_score:.2f}")
                print(f"   Active: {match.active}")
                if match.match_details:
                    print(f"   Details: {match.match_details}")
        else:
            print("No matches found")


def test_multiple_entity_types():
    """Test matching across multiple entity types"""
    print("\n\n" + "=" * 60)
    print("Testing Multiple Entity Type Matching")
    print("=" * 60)

    service = EntityMatchingService()

    query = "Smith"
    entity_types = [EntityType.CONTACT]  # Only contact for now

    print(f"\nSearching for '{query}' across: {[e.value for e in entity_types]}")

    results = service.match_multiple(query, entity_types, with_scoring=True)

    for entity_type, matches in results.items():
        print(f"\n{entity_type.upper()} matches: {len(matches)}")
        for match in matches[:2]:
            print(
                f"  - {match.display_name} (confidence: {match.confidence_score:.2f})"
            )


def test_best_match():
    """Test getting single best match"""
    print("\n\n" + "=" * 60)
    print("Testing Best Match Retrieval")
    print("=" * 60)

    service = EntityMatchingService()

    # Test with high confidence threshold
    query = "john.smith@example.com"
    print(f"\nFinding best match for: '{query}'")

    best_match = service.get_best_match(query, EntityType.CONTACT, min_confidence=0.8)

    if best_match:
        print(f"Best match found: {best_match.display_name}")
        print(f"Confidence: {best_match.confidence_score:.2f}")
        print(f"Type: {best_match.match_type.value}")
    else:
        print("No match meets confidence threshold")


def test_context_boosting():
    """Test context-aware matching"""
    print("\n\n" + "=" * 60)
    print("Testing Context-Aware Matching")
    print("=" * 60)

    service = EntityMatchingService()

    # Test same query with different contexts
    query = "Johnson"

    contexts = [
        None,  # No context
        MatchContext(organization="Mayo Clinic"),
        MatchContext(specialty="Cardiology"),
        MatchContext(organization="Cleveland Clinic", specialty="Neurology"),
    ]

    for context in contexts:
        print(f"\nQuery: '{query}'")
        if context:
            print(
                f"Context: organization={context.organization}, specialty={context.specialty}"
            )
        else:
            print("Context: None")

        matches = service.match_contact(query, context=context)

        if matches:
            match = matches[0]
            print(f"Top match: {match.display_name}")
            print(f"Organization: {match.organization}")
            print(f"Specialty: {match.specialty}")
            print(f"Confidence: {match.confidence_score:.2f}")


def test_supported_entities():
    """Test listing supported entity types"""
    print("\n\n" + "=" * 60)
    print("Supported Entity Types")
    print("=" * 60)

    supported = EntityMatchingService.list_supported_entities()
    print(f"\nCurrently supported: {supported}")


def main():
    """Run all tests"""
    print("Entity Matching Service Test Suite")
    print("==================================\n")

    try:
        test_contact_matching()
        #    test_multiple_entity_types()
        #    test_best_match()
        #    test_context_boosting()
        #    test_supported_entities()

        print("\n\nAll tests completed successfully!")

    except Exception as e:
        print(f"\n\nError during testing: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
