#!/usr/bin/env python3
"""
Manual Email Sync Script

Usage:
    python sync_emails.py                    # Sync last 30 minutes
    python sync_emails.py --minutes 60       # Sync last 60 minutes
    python sync_emails.py --all              # Process all unprocessed emails
    python sync_emails.py --status           # Show sync status
"""

import os
import sys
import argparse
from datetime import datetime

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from services.email_sync_manager import EmailSyncManager


def main():
    parser = argparse.ArgumentParser(description="Sync emails from Nylas")
    parser.add_argument(
        "--minutes", 
        type=int, 
        default=30,
        help="Number of minutes to look back for emails (default: 30)"
    )
    parser.add_argument(
        "--limit", 
        type=int, 
        default=50,
        help="Maximum number of emails to sync (default: 50)"
    )
    parser.add_argument(
        "--all", 
        action="store_true",
        help="Process all unprocessed emails in database"
    )
    parser.add_argument(
        "--status", 
        action="store_true",
        help="Show sync status and exit"
    )
    parser.add_argument(
        "--no-process", 
        action="store_true",
        help="Don't queue emails for AI processing"
    )
    
    args = parser.parse_args()
    
    # Initialize sync manager
    sync_manager = EmailSyncManager()
    
    # Show status and exit if requested
    if args.status:
        status = sync_manager.get_sync_status()
        print("\nEmail Sync Status")
        print("=" * 50)
        print(f"Sync Mode: {status['sync_mode']}")
        print(f"Total Emails: {status['total_emails']}")
        print(f"Unprocessed: {status['unprocessed_emails']}")
        print(f"Last Sync: {status['last_sync'] or 'Never'}")
        print(f"Webhook Configured: {status['webhook_configured']}")
        if status['pinggy_url']:
            print(f"Pinggy URL: {status['pinggy_url']}")
        return
    
    # Process all unprocessed emails
    if args.all:
        print("\nProcessing all unprocessed emails...")
        print("=" * 50)
        results = sync_manager.sync_all_unprocessed_emails()
        print(f"Total unprocessed: {results['total_unprocessed']}")
        print(f"Queued for processing: {results['queued_for_processing']}")
        if results['errors']:
            print(f"Errors: {len(results['errors'])}")
            for error in results['errors']:
                print(f"  - {error}")
        return
    
    # Sync recent emails
    print(f"\nSyncing emails from last {args.minutes} minutes...")
    print("=" * 50)
    
    results = sync_manager.sync_recent_emails(
        minutes_back=args.minutes,
        limit=args.limit,
        process_emails=not args.no_process
    )
    
    # Display results
    print(f"Sync Mode: {results['sync_mode']}")
    print(f"Total Fetched: {results['total_fetched']}")
    print(f"New Emails: {results['new_emails']}")
    print(f"Updated Emails: {results['updated_emails']}")
    
    if results['errors']:
        print(f"\nErrors ({len(results['errors'])}):")
        for error in results['errors']:
            print(f"  - {error}")
    
    print(f"\nSync completed at: {results['sync_time']}")


if __name__ == "__main__":
    main()