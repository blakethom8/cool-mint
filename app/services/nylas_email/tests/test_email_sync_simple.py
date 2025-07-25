#!/usr/bin/env python3
"""
Simple Email Sync Test

This script tests email sync without complex dependencies.
"""

import os
import sys
from datetime import datetime

# Add the app directory to Python path
app_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, app_dir)

from dotenv import load_dotenv
load_dotenv()

from services.nylas_email.config.email_sync_config import EmailSyncConfig


def test_sync_status():
    """Test sync configuration and status"""
    print("\nEmail Sync Configuration Test")
    print("=" * 70)
    
    # Get configuration
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
    
    print("\nMode-specific status:")
    if config['sync_mode'] == 'manual':
        print("  ✓ Manual mode active")
        print("  To sync emails, run:")
        print("    python scripts/sync_emails.py")
    elif config['sync_mode'] == 'webhook':
        if status.get('webhook_ready'):
            print("  ✓ Webhook mode configured and ready")
        else:
            print("  ⚠ Webhook mode selected but not fully configured")
    
    print("\nAvailable Commands:")
    print("  python scripts/sync_emails.py              # Run manual sync")
    print("  python scripts/sync_emails.py --status     # Show sync status")
    print("  python scripts/setup_email_webhook.py      # Start webhook mode")
    print("  python scripts/setup_email_webhook.py --list  # List webhooks")
    

def test_mode_switching():
    """Test mode switching"""
    print("\n\nTesting Mode Switching")
    print("=" * 70)
    
    current_mode = EmailSyncConfig.get_config()["sync_mode"]
    print(f"Current mode: {current_mode}")
    
    # Test switching to webhook mode
    print("\nSwitching to webhook mode...")
    EmailSyncConfig.set_sync_mode("webhook")
    new_mode = EmailSyncConfig.get_config()["sync_mode"]
    print(f"New mode: {new_mode}")
    
    # Switch back
    print(f"\nSwitching back to {current_mode} mode...")
    EmailSyncConfig.set_sync_mode(current_mode)
    final_mode = EmailSyncConfig.get_config()["sync_mode"]
    print(f"Final mode: {final_mode}")


if __name__ == "__main__":
    test_sync_status()
    test_mode_switching()