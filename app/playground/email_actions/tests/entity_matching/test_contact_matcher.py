#!/usr/bin/env python3
"""Test script for contact matching functionality"""
import json
from pathlib import Path
from typing import List, Dict
import argparse

# Add parent directories to path
import sys
sys.path.insert(0, str(Path(__file__).parents[2]))

from contact_matcher import ContactMatcher, ContactMatch
from database.session import db_session
from database.data_models.salesforce_data import SfContact
from utils.base import save_test_result


def create_test_cases() -> List[Dict]:
    """Create comprehensive test cases for contact matching"""
    return [
        # Email matches
        {
            'id': 'email_exact',
            'query': 'john.smith@hospital.org',
            'expected_type': 'email',
            'description': 'Exact email match'
        },
        
        # Name variations
        {
            'id': 'name_with_title',
            'query': 'Dr. Sarah Johnson',
            'expected_type': 'first_last_name',
            'description': 'Name with medical title'
        },
        {
            'id': 'last_name_only',
            'query': 'DeStefano',
            'expected_type': 'last_name',
            'description': 'Last name only search'
        },
        {
            'id': 'full_name_exact',
            'query': 'Michael Chen',
            'expected_type': 'exact_name',
            'description': 'Full name without title'
        },
        
        # Complex cases
        {
            'id': 'name_with_context',
            'query': 'Dr. Johnson',
            'context': {'organization': 'Cedars-Sinai'},
            'expected_type': 'last_name',
            'description': 'Name with organization context'
        },
        {
            'id': 'fuzzy_name',
            'query': 'Sara Jonson',  # Misspelled
            'expected_type': 'fuzzy_name',
            'description': 'Fuzzy matching for misspelled names'
        },
        
        # Special identifiers
        {
            'id': 'npi_match',
            'query': '1234567890',
            'expected_type': 'npi',
            'description': 'NPI number match'
        },
        
        # Edge cases
        {
            'id': 'multiple_titles',
            'query': 'Dr. MD John Smith MD',
            'expected_type': 'first_last_name',
            'description': 'Multiple medical titles'
        },
        {
            'id': 'hyphenated_name',
            'query': 'Mary Johnson-Smith',
            'expected_type': 'exact_name',
            'description': 'Hyphenated last name'
        },
        {
            'id': 'middle_name',
            'query': 'John Michael Smith',
            'expected_type': 'exact_name',
            'description': 'Full name with middle name'
        }
    ]


def test_single_query(matcher: ContactMatcher, query: str, context: Dict = None) -> Dict:
    """Test a single query and return detailed results"""
    matches = matcher.match_contact(query, context)
    
    result = {
        'query': query,
        'context': context,
        'match_count': len(matches),
        'matches': []
    }
    
    for match in matches[:5]:  # Top 5 matches
        match_info = match.to_dict()
        result['matches'].append({
            'name': match_info['name'],
            'email': match_info['email'],
            'specialty': match_info['specialty'],
            'match_type': match_info['match_type'],
            'confidence': match_info['confidence'],
            'details': match_info['details']
        })
    
    return result


def analyze_match_quality(matches: List[ContactMatch], expected_type: str = None) -> Dict:
    """Analyze the quality of matches"""
    analysis = {
        'total_matches': len(matches),
        'confidence_distribution': {},
        'match_types': {},
        'top_confidence': 0,
        'expected_type_found': False
    }
    
    if matches:
        # Confidence distribution
        for match in matches:
            bucket = f"{int(match.confidence_score * 10) / 10:.1f}"
            analysis['confidence_distribution'][bucket] = \
                analysis['confidence_distribution'].get(bucket, 0) + 1
            
            # Match type distribution
            analysis['match_types'][match.match_type] = \
                analysis['match_types'].get(match.match_type, 0) + 1
        
        analysis['top_confidence'] = matches[0].confidence_score
        
        if expected_type:
            analysis['expected_type_found'] = any(
                m.match_type == expected_type for m in matches
            )
    
    return analysis


def run_comprehensive_test():
    """Run comprehensive test suite"""
    matcher = ContactMatcher()
    test_cases = create_test_cases()
    results = []
    
    print("Contact Matcher Comprehensive Test")
    print("=" * 80)
    
    for test_case in test_cases:
        print(f"\nTest: {test_case['description']}")
        print(f"Query: '{test_case['query']}'")
        
        # Run the test
        context = test_case.get('context')
        matches = matcher.match_contact(test_case['query'], context)
        
        # Analyze results
        analysis = analyze_match_quality(matches, test_case.get('expected_type'))
        
        # Display results
        print(f"Found {len(matches)} match(es)")
        if matches:
            top_match = matches[0]
            print(f"Top match: {top_match.contact.name} "
                  f"({top_match.match_type}, confidence: {top_match.confidence_score:.3f})")
        
        if test_case.get('expected_type'):
            status = "✓" if analysis['expected_type_found'] else "✗"
            print(f"Expected type '{test_case['expected_type']}': {status}")
        
        # Store results
        test_result = test_single_query(matcher, test_case['query'], context)
        test_result['test_id'] = test_case['id']
        test_result['description'] = test_case['description']
        test_result['analysis'] = analysis
        results.append(test_result)
    
    # Save results
    filename = save_test_result('contact_matcher_comprehensive', {
        'test_count': len(test_cases),
        'test_results': results
    })
    
    print(f"\n\nResults saved to: results/{filename}")
    
    # Summary statistics
    print("\nSummary Statistics:")
    print("-" * 40)
    total_tests = len(results)
    tests_with_matches = sum(1 for r in results if r['match_count'] > 0)
    tests_with_expected = sum(1 for r in results if r.get('analysis', {}).get('expected_type_found'))
    
    print(f"Total tests: {total_tests}")
    print(f"Tests with matches: {tests_with_matches} ({tests_with_matches/total_tests*100:.1f}%)")
    print(f"Tests with expected type: {tests_with_expected}")


def interactive_test():
    """Interactive testing mode"""
    matcher = ContactMatcher()
    
    print("\nInteractive Contact Matcher Test")
    print("=" * 60)
    print("Enter queries to test contact matching.")
    print("Format: <query> [from <organization>]")
    print("Type 'quit' to exit\n")
    
    while True:
        query = input("Query: ").strip()
        
        if query.lower() == 'quit':
            break
        
        if not query:
            continue
        
        # Parse context
        context = None
        if ' from ' in query.lower():
            parts = query.split(' from ', 1)
            query = parts[0].strip()
            context = {'organization': parts[1].strip()}
        
        # Run match
        matches = matcher.match_contact(query, context)
        
        # Display results
        if matches:
            print(f"\nFound {len(matches)} match(es):")
            for i, match in enumerate(matches[:5]):
                print(f"\n{i+1}. {match.contact.name}")
                print(f"   Type: {match.match_type}")
                print(f"   Confidence: {match.confidence_score:.3f}")
                print(f"   Email: {match.contact.email or 'N/A'}")
                print(f"   Specialty: {match.contact.specialty or 'N/A'}")
                if match.match_details:
                    print(f"   Details: {match.match_details}")
        else:
            print("\nNo matches found")
        
        print("\n" + "-" * 60 + "\n")


def test_specific_contact(contact_id: str):
    """Test matching for a specific contact"""
    for session in db_session():
        contact = session.query(SfContact).filter(
            SfContact.salesforce_id == contact_id
        ).first()
        
        if not contact:
            print(f"Contact {contact_id} not found")
            return
        
        print(f"\nTesting matches for: {contact.name}")
        print(f"Email: {contact.email}")
        print(f"Specialty: {contact.specialty}")
        print("-" * 60)
        
        matcher = ContactMatcher()
        
        # Test different query variations
        test_queries = [
            contact.email,
            contact.name,
            contact.last_name,
            f"Dr. {contact.last_name}",
            f"{contact.first_name} {contact.last_name}",
        ]
        
        if contact.npi:
            test_queries.append(contact.npi)
        
        for query in test_queries:
            if query:
                print(f"\nQuery: '{query}'")
                matches = matcher.match_contact(query)
                
                found_self = any(m.contact.id == contact.id for m in matches)
                print(f"Found self: {'✓' if found_self else '✗'}")
                
                if matches:
                    top_match = matches[0]
                    print(f"Top match: {top_match.contact.name} "
                          f"(confidence: {top_match.confidence_score:.3f})")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Test contact matcher')
    parser.add_argument('--mode', choices=['comprehensive', 'interactive', 'specific'],
                       default='comprehensive',
                       help='Test mode to run')
    parser.add_argument('--contact-id', help='Salesforce ID for specific contact test')
    
    args = parser.parse_args()
    
    if args.mode == 'comprehensive':
        run_comprehensive_test()
    elif args.mode == 'interactive':
        interactive_test()
    elif args.mode == 'specific':
        if args.contact_id:
            test_specific_contact(args.contact_id)
        else:
            print("Error: --contact-id required for specific mode")
    else:
        # Default: run comprehensive test
        run_comprehensive_test()