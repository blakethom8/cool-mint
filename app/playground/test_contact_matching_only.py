#!/usr/bin/env python3
"""Test script for contact matching functionality only"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment
load_dotenv()

from services.entity_matching import (
    EntityMatchingService,
    EntityType,
    MatchContext
)


def test_contact_matching():
    """Test contact matching functionality"""
    print("=" * 60)
    print("Testing Contact Matching Service")
    print("=" * 60)
    
    # Initialize service
    service = EntityMatchingService()
    
    # Test cases
    test_queries = [
        # Email matching
        {
            "query": "john.smith@example.com",
            "description": "Email match"
        },
        # Name matching
        {
            "query": "Dr. DeStefano",
            "description": "Name with title"
        },
        # Last name only
        {
            "query": "Smith",
            "description": "Last name only"
        },
        # NPI matching
        {
            "query": "1234567890",
            "description": "NPI match (if exists)"
        },
        # Name with context
        {
            "query": "Smith",
            "context": {"organization": "Cardiology Associates"},
            "description": "Last name with organization context"
        }
    ]
    
    for test in test_queries:
        print(f"\n{test['description']}: '{test['query']}'")
        print("-" * 40)
        
        context = test.get('context')
        if context:
            print(f"Context: {context}")
        
        # Use convenience method
        matches = service.match_contact(
            test['query'],
            context=context,
            with_scoring=True
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
    
    print("\n" + "=" * 60)
    print("Contact matching test completed!")
    print("=" * 60)


if __name__ == "__main__":
    test_contact_matching()