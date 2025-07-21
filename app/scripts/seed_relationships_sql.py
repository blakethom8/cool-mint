#!/usr/bin/env python3
"""
Script to seed relationships table using raw SQL to avoid ORM circular imports.
"""

import sys
import os
import argparse
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from uuid import uuid4
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.session import SessionLocal
from sqlalchemy import text


def seed_relationships_sql(include_employed=True, include_community=True):
    """Seed relationships using raw SQL."""
    db = SessionLocal()
    
    try:
        print("Loading lookup data...")
        
        # Load lookup tables
        status_map = {}
        result = db.execute(text("SELECT id, code FROM relationship_status_types"))
        for row in result:
            status_map[row.code] = row.id
            
        loyalty_map = {}
        result = db.execute(text("SELECT id, code FROM loyalty_status_types"))
        for row in result:
            loyalty_map[row.code] = row.id
            
        entity_type_map = {}
        result = db.execute(text("SELECT id, code FROM entity_types"))
        for row in result:
            entity_type_map[row.code] = row.id
        
        print(f"Loaded {len(status_map)} statuses, {len(loyalty_map)} loyalty types, {len(entity_type_map)} entity types")
        
        # Extract relationships from activities
        print("\nExtracting relationships from activities...")
        
        activities = db.execute(text("""
            SELECT 
                owner_id,
                activity_date,
                llm_context_json,
                mno_type,
                priority
            FROM sf_activities_structured
            WHERE llm_context_json IS NOT NULL
            ORDER BY activity_date DESC
        """)).fetchall()
        
        relationships = defaultdict(lambda: {
            'activities': [],
            'employment_statuses': set(),
            'contact_name': None,
            'last_activity': None,
            'first_activity': None,
            'activity_count': 0,
            'high_priority_count': 0,
            'last_90_days_count': 0
        })
        
        today = datetime.now().date()
        ninety_days_ago = today - timedelta(days=90)
        
        for activity in activities:
            if not activity.llm_context_json or 'contacts' not in activity.llm_context_json:
                continue
                
            for contact in activity.llm_context_json.get('contacts', []):
                contact_sf_id = contact.get('contact_id')
                if not contact_sf_id:
                    continue
                
                # Check employment filter
                employment_status = contact.get('employment_status', 'Unknown')
                if employment_status == 'Employed' and not include_employed:
                    continue
                if employment_status in ['Community', 'Out of Network'] and not include_community:
                    continue
                    
                key = (activity.owner_id, contact_sf_id)
                rel = relationships[key]
                
                # Track activity
                rel['activities'].append(activity.activity_date)
                rel['activity_count'] += 1
                
                if activity.priority == 'High':
                    rel['high_priority_count'] += 1
                    
                if activity.activity_date >= ninety_days_ago:
                    rel['last_90_days_count'] += 1
                
                # Track contact details
                rel['employment_statuses'].add(employment_status)
                rel['contact_name'] = contact.get('contact_name')
                
                # Update dates
                if not rel['first_activity'] or activity.activity_date < rel['first_activity']:
                    rel['first_activity'] = activity.activity_date
                if not rel['last_activity'] or activity.activity_date > rel['last_activity']:
                    rel['last_activity'] = activity.activity_date
        
        print(f"Found {len(relationships)} unique relationships")
        
        # Create relationship records
        print("\nCreating relationship records...")
        
        created_count = 0
        updated_count = 0
        skipped_count = 0
        
        for (owner_sf_id, contact_sf_id), rel_data in relationships.items():
            # Look up user
            user_result = db.execute(text(
                "SELECT id FROM sf_users WHERE salesforce_id = :sf_id"
            ), {"sf_id": owner_sf_id}).first()
            
            if not user_result:
                skipped_count += 1
                continue
                
            # Look up contact
            contact_result = db.execute(text(
                "SELECT id FROM sf_contacts WHERE salesforce_id = :sf_id"
            ), {"sf_id": contact_sf_id}).first()
            
            if not contact_result:
                skipped_count += 1
                continue
            
            # Calculate status
            days_since = (today - rel_data['last_activity']).days
            recent_count = rel_data['last_90_days_count']
            
            if days_since > 180:
                status_id = status_map['DEPRIORITIZED']
            elif recent_count > 5:
                status_id = status_map['ESTABLISHED']
            elif recent_count >= 2:
                status_id = status_map['BUILDING']
            else:
                status_id = status_map['PROSPECTING']
            
            # Calculate lead score
            score = 3
            if rel_data['activity_count'] >= 10:
                score += 1
            elif rel_data['activity_count'] <= 1:
                score -= 1
                
            if days_since <= 30:
                score += 1
            elif days_since > 180:
                score -= 1
                
            if rel_data['high_priority_count'] >= 3:
                score += 1
                
            lead_score = max(1, min(5, score))
            
            # Check if relationship exists
            existing = db.execute(text("""
                SELECT relationship_id FROM relationships 
                WHERE user_id = :user_id 
                AND entity_type_id = :entity_type_id 
                AND linked_entity_id = :linked_entity_id
            """), {
                "user_id": user_result.id,
                "entity_type_id": entity_type_map['SfContact'],
                "linked_entity_id": contact_result.id
            }).first()
            
            if existing:
                # Update existing
                db.execute(text("""
                    UPDATE relationships 
                    SET last_activity_date = :last_activity,
                        relationship_status_id = :status_id,
                        lead_score = :lead_score,
                        updated_at = NOW()
                    WHERE relationship_id = :id
                """), {
                    "last_activity": rel_data['last_activity'],
                    "status_id": status_id,
                    "lead_score": lead_score,
                    "id": existing.relationship_id
                })
                updated_count += 1
            else:
                # Create new
                db.execute(text("""
                    INSERT INTO relationships (
                        relationship_id, user_id, entity_type_id, linked_entity_id,
                        relationship_status_id, loyalty_status_id, lead_score,
                        last_activity_date, created_at, updated_at
                    ) VALUES (
                        :id, :user_id, :entity_type_id, :linked_entity_id,
                        :status_id, :loyalty_id, :lead_score,
                        :last_activity, NOW(), NOW()
                    )
                """), {
                    "id": uuid4(),
                    "user_id": user_result.id,
                    "entity_type_id": entity_type_map['SfContact'],
                    "linked_entity_id": contact_result.id,
                    "status_id": status_id,
                    "loyalty_id": loyalty_map['UNKNOWN'],
                    "lead_score": lead_score,
                    "last_activity": rel_data['last_activity']
                })
                created_count += 1
        
        db.commit()
        
        # Generate report
        report = {
            'total_relationships': len(relationships),
            'records_created': created_count,
            'records_updated': updated_count,
            'records_skipped': skipped_count,
            'timestamp': datetime.now().isoformat()
        }
        
        return report
        
    except Exception as e:
        db.rollback()
        raise
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description='Seed relationships table')
    
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--all', action='store_true', default=True,
                      help='Include all contacts (default)')
    group.add_argument('--community', action='store_true',
                      help='Only community/out-of-network contacts')
    group.add_argument('--employed', action='store_true',
                      help='Only employed contacts')
    
    args = parser.parse_args()
    
    if args.community:
        include_employed = False
        include_community = True
        filter_desc = "community/out-of-network only"
    elif args.employed:
        include_employed = True
        include_community = False
        filter_desc = "employed only"
    else:
        include_employed = True
        include_community = True
        filter_desc = "all contacts"
    
    print(f"\n{'='*60}")
    print(f"Relationship Seeding Script (SQL Version)")
    print(f"{'='*60}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Filter: {filter_desc}")
    print(f"{'='*60}\n")
    
    try:
        report = seed_relationships_sql(include_employed, include_community)
        
        print(f"\n{'='*60}")
        print("SUCCESS")
        print(f"{'='*60}")
        print(f"Total relationships: {report['total_relationships']:,}")
        print(f"Created: {report['records_created']:,}")
        print(f"Updated: {report['records_updated']:,}")
        print(f"Skipped: {report['records_skipped']:,}")
        print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()