#!/usr/bin/env python3
"""
Analyze activity patterns using raw SQL to avoid circular import issues.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from collections import defaultdict, Counter
import json
from typing import Dict, List, Tuple
from sqlalchemy import text
from database.session import SessionLocal


def analyze_activity_patterns():
    """Main analysis function to understand activity patterns."""
    db = SessionLocal()
    
    try:
        print("=== Activity Pattern Analysis ===\n")
        
        # 1. Total activities and date range
        result = db.execute(text("""
            SELECT 
                COUNT(*) as total,
                MIN(activity_date) as min_date,
                MAX(activity_date) as max_date
            FROM sf_activities_structured
        """)).first()
        
        print(f"Total Activities: {result.total:,}")
        print(f"Date Range: {result.min_date} to {result.max_date}")
        days_covered = (result.max_date - result.min_date).days if result.min_date and result.max_date else 0
        print(f"Days Covered: {days_covered}")
        
        # 2. Unique users with activities
        result = db.execute(text("SELECT COUNT(DISTINCT owner_id) FROM sf_activities_structured")).scalar()
        print(f"\nUnique Users with Activities: {result}")
        
        # 3. Extract user-contact relationships from llm_context_json
        print("\n=== Analyzing User-Contact Relationships ===")
        
        # Query all activities with their JSON data
        activities = db.execute(text("""
            SELECT 
                owner_id,
                activity_date,
                llm_context_json,
                mno_type,
                mno_subtype
            FROM sf_activities_structured
            WHERE llm_context_json IS NOT NULL
        """)).fetchall()
        
        # Track unique relationships and their details
        relationships = defaultdict(lambda: {
            'activities': [],
            'employment_statuses': set(),
            'is_physician': False,
            'specialties': set(),
            'contact_name': None,
            'last_activity': None,
            'first_activity': None,
            'activity_count': 0,
            'mno_types': Counter()
        })
        
        contacts_by_employment = {'Employed': set(), 'Community': set(), 'Out of Network': set(), 'Unknown': set()}
        
        for activity in activities:
            if not activity.llm_context_json or 'contacts' not in activity.llm_context_json:
                continue
                
            for contact in activity.llm_context_json['contacts']:
                contact_id = contact.get('contact_id')
                if not contact_id:
                    continue
                    
                key = (activity.owner_id, contact_id)
                rel = relationships[key]
                
                # Track activity
                rel['activities'].append(activity.activity_date)
                rel['activity_count'] += 1
                rel['mno_types'][activity.mno_type] += 1
                
                # Track contact details
                employment_status = contact.get('employment_status', 'Unknown')
                if employment_status is None:
                    employment_status = 'Unknown'
                rel['employment_statuses'].add(employment_status)
                if employment_status not in contacts_by_employment:
                    contacts_by_employment[employment_status] = set()
                contacts_by_employment[employment_status].add(contact_id)
                
                rel['is_physician'] = contact.get('is_physician', False)
                if contact.get('mn_specialty_group'):
                    rel['specialties'].add(contact['mn_specialty_group'])
                rel['contact_name'] = contact.get('contact_name')
                
                # Update date range
                if not rel['first_activity'] or activity.activity_date < rel['first_activity']:
                    rel['first_activity'] = activity.activity_date
                if not rel['last_activity'] or activity.activity_date > rel['last_activity']:
                    rel['last_activity'] = activity.activity_date
        
        print(f"\nTotal Unique User-Contact Relationships: {len(relationships):,}")
        
        # 4. Employment Status Breakdown
        print("\n=== Contact Employment Status Breakdown ===")
        for status, contacts in contacts_by_employment.items():
            print(f"{status}: {len(contacts):,} unique contacts")
        
        # 5. Activity Frequency Distribution
        print("\n=== Activity Frequency Distribution ===")
        frequency_dist = Counter()
        for rel in relationships.values():
            count = rel['activity_count']
            if count == 1:
                bucket = '1 activity'
            elif count <= 5:
                bucket = '2-5 activities'
            elif count <= 10:
                bucket = '6-10 activities'
            elif count <= 20:
                bucket = '11-20 activities'
            else:
                bucket = '20+ activities'
            frequency_dist[bucket] += 1
        
        bucket_order = ['1 activity', '2-5 activities', '6-10 activities', '11-20 activities', '20+ activities']
        for bucket in bucket_order:
            count = frequency_dist.get(bucket, 0)
            pct = (count / len(relationships)) * 100 if relationships else 0
            print(f"{bucket}: {count:,} relationships ({pct:.1f}%)")
        
        # 6. Time-based Analysis
        print("\n=== Activity Recency Analysis ===")
        today = datetime.now().date()
        recency_dist = Counter()
        
        for rel in relationships.values():
            if not rel['last_activity']:
                continue
                
            days_since_last = (today - rel['last_activity']).days
            
            if days_since_last <= 30:
                bucket = 'Last 30 days'
            elif days_since_last <= 90:
                bucket = 'Last 31-90 days'
            elif days_since_last <= 180:
                bucket = 'Last 91-180 days'
            elif days_since_last <= 365:
                bucket = 'Last 181-365 days'
            else:
                bucket = 'Over 1 year ago'
            
            recency_dist[bucket] += 1
        
        for bucket in ['Last 30 days', 'Last 31-90 days', 'Last 91-180 days', 
                      'Last 181-365 days', 'Over 1 year ago']:
            count = recency_dist.get(bucket, 0)
            pct = (count / len(relationships)) * 100 if relationships else 0
            print(f"{bucket}: {count:,} relationships ({pct:.1f}%)")
        
        # 7. Most Active Relationships
        print("\n=== Top 10 Most Active Relationships ===")
        sorted_rels = sorted(relationships.items(), 
                           key=lambda x: x[1]['activity_count'], 
                           reverse=True)[:10]
        
        for (owner_id, contact_id), rel in sorted_rels:
            # Look up user name
            user_result = db.execute(text(
                "SELECT name FROM sf_users WHERE salesforce_id = :owner_id"
            ), {"owner_id": owner_id}).first()
            user_name = user_result.name if user_result else owner_id
            
            print(f"\n{user_name} <-> {rel['contact_name'] or contact_id}")
            print(f"  Activities: {rel['activity_count']}")
            print(f"  Employment: {', '.join(rel['employment_statuses'])}")
            print(f"  Date Range: {rel['first_activity']} to {rel['last_activity']}")
            print(f"  Top Activity Types: {dict(rel['mno_types'].most_common(3))}")
        
        # 8. Proposed Status Distribution (using business rules)
        print("\n=== Proposed Relationship Status Distribution ===")
        print("(Based on activity count in last 90 days)")
        status_dist = Counter()
        
        for rel in relationships.values():
            days_since = (today - rel['last_activity']).days if rel['last_activity'] else 999
            
            # Count activities in last 90 days
            recent_activities = sum(1 for d in rel['activities'] if (today - d).days <= 90)
            
            if days_since > 180:
                status = 'DEPRIORITIZED'
            elif recent_activities > 5:
                status = 'ESTABLISHED'
            elif recent_activities >= 2:
                status = 'BUILDING'
            else:
                status = 'PROSPECTING'
            
            status_dist[status] += 1
        
        for status in ['ESTABLISHED', 'BUILDING', 'PROSPECTING', 'DEPRIORITIZED']:
            count = status_dist.get(status, 0)
            pct = (count / len(relationships)) * 100 if relationships else 0
            print(f"{status}: {count:,} relationships ({pct:.1f}%)")
        
        # 9. Focus on Community (non-employed) contacts
        print("\n=== Community Contact Analysis ===")
        community_rels = {k: v for k, v in relationships.items() 
                         if 'Community' in v['employment_statuses'] or 'Out of Network' in v['employment_statuses']}
        print(f"Total Community/Out of Network Relationships: {len(community_rels):,}")
        print(f"Percentage of all relationships: {(len(community_rels)/len(relationships)*100):.1f}%")
        
        # 10. Summary Recommendations
        print("\n=== Summary & Recommendations ===")
        print(f"1. Total relationships to seed: {len(relationships):,}")
        print(f"2. Community-focused relationships: {len(community_rels):,}")
        print(f"3. Active relationships (last 90 days): {sum(1 for r in relationships.values() if r['last_activity'] and (today - r['last_activity']).days <= 90):,}")
        print(f"4. Relationships needing reactivation (91-180 days): {sum(1 for r in relationships.values() if r['last_activity'] and 90 < (today - r['last_activity']).days <= 180):,}")
        print(f"5. Consider separate handling for Employed vs Community contacts")
        print(f"6. Most activities are MD-to-MD visits, indicating physician outreach focus")
        
    except Exception as e:
        print(f"Error during analysis: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    analyze_activity_patterns()