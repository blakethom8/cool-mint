#!/usr/bin/env python3
"""
Email Sync Management Tool

A unified interface for managing email synchronization.

Usage:
    python manage_email_sync.py status              # Show current status
    python manage_email_sync.py mode manual         # Switch to manual mode
    python manage_email_sync.py mode webhook        # Switch to webhook mode
    python manage_email_sync.py sync                # Run manual sync
    python manage_email_sync.py webhook start       # Start webhook with Pinggy
    python manage_email_sync.py webhook list        # List webhooks
    python manage_email_sync.py webhook cleanup     # Delete all webhooks
"""

import os
import sys
import argparse
from datetime import datetime

# Add the app directory to Python path
app_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, app_dir)

from dotenv import load_dotenv
load_dotenv()

from services.nylas_email.config.email_sync_config import EmailSyncConfig
from services.email_sync_manager import EmailSyncManager
from services.nylas_email.scripts.setup_email_webhook import WebhookManager


def show_status():
    """Show comprehensive email sync status"""
    print("\nEmail Sync Status")
    print("=" * 70)
    
    # Get configuration status
    status = EmailSyncConfig.get_status()
    config = status["config"]
    env = status["environment"]
    
    print(f"Current Mode: {config['sync_mode'].upper()}")
    print(f"Process on Sync: {config['process_on_sync']}")
    print(f"Batch Size: {config['batch_size']}")
    print(f"Lookback Minutes: {config['sync_lookback_minutes']}")
    
    print("\nEnvironment Status:")
    print(f"  Nylas API: {'✓' if env['nylas_configured'] else '✗'}")
    print(f"  Grant ID: {'✓' if env['grant_id_configured'] else '✗'}")
    print(f"  Webhook Secret: {'✓' if env['webhook_secret_configured'] else '✗'}")
    print(f"  Server URL: {'✓' if env['server_url_configured'] else '✗'}")
    
    # Get database status
    sync_manager = EmailSyncManager()
    db_status = sync_manager.get_sync_status()
    
    print("\nDatabase Status:")
    print(f"  Total Emails: {db_status['total_emails']}")
    print(f"  Unprocessed: {db_status['unprocessed_emails']}")
    print(f"  Last Sync: {db_status['last_sync'] or 'Never'}")
    
    # Mode-specific recommendations
    print("\nRecommendations:")
    if config['sync_mode'] == 'webhook':
        if not env['webhook_secret_configured'] or not env['server_url_configured']:
            print("  ⚠ Run 'manage_email_sync.py webhook start' to configure webhook")
        else:
            print("  ✓ Webhook mode is configured")
            print(f"  Server URL: {os.environ.get('SERVER_URL')}")
    elif config['sync_mode'] == 'manual':
        print("  ✓ Manual mode active - run 'sync' command to fetch emails")
    
    print()


def set_mode(mode: str):
    """Set the email sync mode"""
    try:
        EmailSyncConfig.set_sync_mode(mode)
        print(f"✓ Sync mode set to: {mode}")
        
        if mode == "webhook":
            print("\nNext steps for webhook mode:")
            print("1. Ensure your FastAPI server is running on port 8080")
            print("2. Run: python manage_email_sync.py webhook start")
        elif mode == "manual":
            print("\nManual mode active. Run sync with:")
            print("  python manage_email_sync.py sync")
        
    except ValueError as e:
        print(f"✗ Error: {e}")
        sys.exit(1)


def handle_webhook_command(args):
    """Handle webhook-related commands"""
    manager = WebhookManager()
    
    if args.webhook_action == "start":
        print("Starting webhook mode...")
        print("Make sure your FastAPI server is running on port 8080!")
        print()
        manager.run_webhook_mode(port=8080)
    elif args.webhook_action == "list":
        manager.list_webhooks()
    elif args.webhook_action == "cleanup":
        manager.cleanup_old_webhooks()
        print("✓ All webhooks cleaned up")


def run_sync(args):
    """Run manual email sync"""
    if EmailSyncConfig.is_webhook_mode():
        print("⚠ Warning: System is in webhook mode. Switching to manual mode...")
        EmailSyncConfig.set_sync_mode("manual")
    
    # Run sync
    sync_manager = EmailSyncManager()
    results = sync_manager.sync_recent_emails(
        minutes_back=args.minutes,
        limit=args.limit,
        process_emails=args.process
    )
    
    # Display results
    print(f"\nSync completed at: {results['sync_time']}")
    print(f"New Emails: {results['new_emails']}")
    print(f"Updated: {results['updated_emails']}")
    if results['errors']:
        print(f"Errors: {len(results['errors'])}")


def main():
    parser = argparse.ArgumentParser(
        description="Manage email synchronization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s status                    # Show current status
  %(prog)s mode manual               # Switch to manual sync mode
  %(prog)s mode webhook              # Switch to webhook mode
  %(prog)s sync                      # Run manual sync (last 30 min)
  %(prog)s sync --minutes 60         # Sync last 60 minutes
  %(prog)s webhook start             # Start webhook with Pinggy
  %(prog)s webhook list              # List all webhooks
  %(prog)s webhook cleanup           # Delete all webhooks
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Status command
    subparsers.add_parser("status", help="Show sync status")
    
    # Mode command
    mode_parser = subparsers.add_parser("mode", help="Set sync mode")
    mode_parser.add_argument(
        "sync_mode", 
        choices=["manual", "webhook", "scheduled"],
        help="Sync mode to set"
    )
    
    # Sync command
    sync_parser = subparsers.add_parser("sync", help="Run manual sync")
    sync_parser.add_argument(
        "--minutes", 
        type=int, 
        default=30,
        help="Minutes to look back (default: 30)"
    )
    sync_parser.add_argument(
        "--limit", 
        type=int, 
        default=50,
        help="Max emails to sync (default: 50)"
    )
    sync_parser.add_argument(
        "--no-process", 
        dest="process",
        action="store_false",
        help="Don't queue for processing"
    )
    
    # Webhook command
    webhook_parser = subparsers.add_parser("webhook", help="Manage webhooks")
    webhook_parser.add_argument(
        "webhook_action",
        choices=["start", "list", "cleanup"],
        help="Webhook action"
    )
    
    args = parser.parse_args()
    
    # Execute command
    if not args.command:
        parser.print_help()
    elif args.command == "status":
        show_status()
    elif args.command == "mode":
        set_mode(args.sync_mode)
    elif args.command == "sync":
        run_sync(args)
    elif args.command == "webhook":
        handle_webhook_command(args)


if __name__ == "__main__":
    main()