#!/usr/bin/env python3
"""
Verify the seeded relationships data.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.session import SessionLocal
from sqlalchemy import text


def verify_relationships():
    db = SessionLocal()
    
    try:
        print("\n=== Relationship Data Verification ===\n")
        
        # Total relationships
        total = db.execute(text("SELECT COUNT(*) FROM relationships")).scalar()
        print(f"Total Relationships: {total:,}")
        
        # By status
        print("\nRelationships by Status:")
        result = db.execute(text("""
            SELECT rst.code, rst.display_name, COUNT(*) as count
            FROM relationships r
            JOIN relationship_status_types rst ON r.relationship_status_id = rst.id
            GROUP BY rst.code, rst.display_name
            ORDER BY COUNT(*) DESC
        """))
        for row in result:
            print(f"  {row.display_name}: {row.count:,}")
        
        # By loyalty
        print("\nRelationships by Loyalty Status:")
        result = db.execute(text("""
            SELECT lst.code, lst.display_name, COUNT(*) as count
            FROM relationships r
            JOIN loyalty_status_types lst ON r.loyalty_status_id = lst.id
            GROUP BY lst.code, lst.display_name
            ORDER BY COUNT(*) DESC
        """))
        for row in result:
            print(f"  {row.display_name}: {row.count:,}")
        
        # By lead score
        print("\nRelationships by Lead Score:")
        result = db.execute(text("""
            SELECT lead_score, COUNT(*) as count
            FROM relationships
            GROUP BY lead_score
            ORDER BY lead_score DESC
        """))
        for row in result:
            print(f"  Score {row.lead_score}: {row.count:,}")
        
        # By user
        print("\nTop 5 Users by Relationship Count:")
        result = db.execute(text("""
            SELECT u.name, COUNT(*) as count
            FROM relationships r
            JOIN sf_users u ON r.user_id = u.id
            GROUP BY u.name
            ORDER BY COUNT(*) DESC
            LIMIT 5
        """))
        for row in result:
            print(f"  {row.name}: {row.count:,} relationships")
        
        # Sample relationships
        print("\nSample Relationships (first 5):")
        result = db.execute(text("""
            SELECT 
                u.name as user_name,
                c.name as contact_name,
                rst.display_name as status,
                r.lead_score,
                r.last_activity_date
            FROM relationships r
            JOIN sf_users u ON r.user_id = u.id
            JOIN sf_contacts c ON r.linked_entity_id = c.id
            JOIN relationship_status_types rst ON r.relationship_status_id = rst.id
            ORDER BY r.created_at DESC
            LIMIT 5
        """))
        
        for row in result:
            print(f"\n  {row.user_name} <-> {row.contact_name}")
            print(f"    Status: {row.status}")
            print(f"    Lead Score: {row.lead_score}")
            print(f"    Last Activity: {row.last_activity_date.strftime('%Y-%m-%d')}")
        
        print("\n=== Verification Complete ===\n")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    verify_relationships()