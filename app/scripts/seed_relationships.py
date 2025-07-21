#!/usr/bin/env python3
"""
Script to seed the relationships table from historical activity data.

Usage:
    python seed_relationships.py [--all|--community|--employed]
    
Options:
    --all: Include all contacts (default)
    --community: Only include community/out-of-network contacts
    --employed: Only include employed contacts
"""

import sys
import os
import argparse
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.relationship_seeding_service import run_seeding


def main():
    parser = argparse.ArgumentParser(description='Seed relationships table from activity data')
    
    # Create mutually exclusive group for filtering options
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--all', action='store_true', default=True,
                      help='Include all contacts (default)')
    group.add_argument('--community', action='store_true',
                      help='Only include community/out-of-network contacts')
    group.add_argument('--employed', action='store_true',
                      help='Only include employed contacts')
    
    args = parser.parse_args()
    
    # Determine filter settings
    if args.community:
        include_employed = False
        include_community = True
        filter_desc = "community/out-of-network contacts only"
    elif args.employed:
        include_employed = True
        include_community = False
        filter_desc = "employed contacts only"
    else:
        include_employed = True
        include_community = True
        filter_desc = "all contacts"
    
    print(f"\n{'='*60}")
    print(f"Relationship Seeding Script")
    print(f"{'='*60}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Filter: {filter_desc}")
    print(f"{'='*60}\n")
    
    try:
        # Run the seeding process
        report = run_seeding(
            include_employed=include_employed,
            include_community=include_community
        )
        
        # Display results
        print(f"\n{'='*60}")
        print("SEEDING COMPLETED SUCCESSFULLY")
        print(f"{'='*60}")
        print(f"\nSummary Report:")
        print(f"  Total relationships analyzed: {report['total_relationships']:,}")
        print(f"  Records created/updated: {report['records_created']:,}")
        print(f"  Employed-only relationships: {report['employed_only_count']:,}")
        print(f"  Community-involved relationships: {report['community_involved_count']:,}")
        print(f"  Active (last 90 days): {report['active_last_90_days']:,}")
        
        print(f"\nStatus Distribution:")
        for status, count in report['status_distribution'].items():
            pct = (count / report['total_relationships']) * 100
            print(f"  {status}: {count:,} ({pct:.1f}%)")
        
        print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
        
    except Exception as e:
        print(f"\n{'!'*60}")
        print(f"ERROR: Seeding failed!")
        print(f"{'!'*60}")
        print(f"Error details: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()