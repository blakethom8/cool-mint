#!/usr/bin/env python3
"""Simple test for contact matching without ORM complications"""
import os
import sys
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parents[2]))

# Set up minimal environment
os.environ['PYTHONPATH'] = str(Path(__file__).parents[2])

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# Direct database connection
DATABASE_HOST = os.getenv("DATABASE_HOST", "localhost")
DATABASE_NAME = os.getenv("DATABASE_NAME", "postgres")
DATABASE_USER = os.getenv("DATABASE_USER", "postgres")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
DATABASE_PORT = os.getenv("DATABASE_PORT", "5433")

DATABASE_URL = f"postgresql://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)


def search_contacts_simple(query: str):
    """Simple contact search using raw SQL"""
    session = Session()
    
    try:
        # Clean the query
        query_clean = query.strip()
        
        print(f"\nSearching for: '{query_clean}'")
        print("-" * 60)
        
        # Try email match first
        if '@' in query_clean:
            result = session.execute(text("""
                SELECT id, salesforce_id, name, email, specialty, active
                FROM sf_contacts
                WHERE LOWER(email) = LOWER(:query)
                LIMIT 5
            """), {"query": query_clean})
            
            matches = result.fetchall()
            if matches:
                print(f"\nEmail matches found: {len(matches)}")
                for match in matches:
                    print(f"  - {match.name} ({match.email})")
                    print(f"    Specialty: {match.specialty}")
                return
        
        # Try name matching
        # Remove common titles
        name_query = query_clean.lower()
        for title in ['dr.', 'dr', 'md', 'do', 'phd']:
            name_query = name_query.replace(title, '').strip()
        
        # Last name only search
        if ' ' not in name_query:
            result = session.execute(text("""
                SELECT id, salesforce_id, name, email, specialty, active
                FROM sf_contacts
                WHERE LOWER(last_name) = :query
                OR LOWER(name) LIKE :pattern
                LIMIT 10
            """), {
                "query": name_query,
                "pattern": f"%{name_query}%"
            })
        else:
            # Multi-part name
            parts = name_query.split()
            first = parts[0]
            last = parts[-1]
            
            result = session.execute(text("""
                SELECT id, salesforce_id, name, email, specialty, active
                FROM sf_contacts
                WHERE (LOWER(first_name) = :first AND LOWER(last_name) = :last)
                OR LOWER(name) = :full_name
                OR LOWER(name) LIKE :pattern
                LIMIT 10
            """), {
                "first": first,
                "last": last,
                "full_name": name_query,
                "pattern": f"%{name_query}%"
            })
        
        matches = result.fetchall()
        
        if matches:
            print(f"\nName matches found: {len(matches)}")
            for i, match in enumerate(matches, 1):
                print(f"\n{i}. {match.name}")
                print(f"   Email: {match.email or 'N/A'}")
                print(f"   Specialty: {match.specialty or 'N/A'}")
                print(f"   Active: {'Yes' if match.active else 'No'}")
        else:
            print("\nNo matches found")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        session.close()


def test_basic_queries():
    """Test basic contact queries"""
    test_queries = [
        "johnson",
        "Dr. Smith",
        "sarah.johnson@example.com",
        "Michael Chen",
        "DeStefano"
    ]
    
    print("Simple Contact Search Test")
    print("=" * 80)
    
    for query in test_queries:
        search_contacts_simple(query)
        print("\n" + "=" * 80)


def count_contacts():
    """Count total contacts in database"""
    session = Session()
    try:
        result = session.execute(text("SELECT COUNT(*) as count FROM sf_contacts"))
        count = result.scalar()
        print(f"\nTotal contacts in database: {count}")
        
        # Count active contacts
        result = session.execute(text("SELECT COUNT(*) as count FROM sf_contacts WHERE active = true"))
        active_count = result.scalar()
        print(f"Active contacts: {active_count}")
        
        # Count with email
        result = session.execute(text("SELECT COUNT(*) as count FROM sf_contacts WHERE email IS NOT NULL"))
        email_count = result.scalar()
        print(f"Contacts with email: {email_count}")
        
    except Exception as e:
        print(f"Error counting contacts: {e}")
    finally:
        session.close()


if __name__ == '__main__':
    count_contacts()
    print("\n" + "=" * 80)
    test_basic_queries()