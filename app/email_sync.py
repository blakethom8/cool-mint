#!/usr/bin/env python3
"""
Email Sync Launcher

Simple launcher for email sync functionality.

Usage:
    python email_sync.py status        # Check sync status
    python email_sync.py sync          # Run manual sync
    python email_sync.py webhook       # Start webhook mode
    python email_sync.py test          # Test configuration
"""

import sys
import os

# Determine which script to run based on command
if len(sys.argv) < 2:
    print(__doc__)
    sys.exit(1)

command = sys.argv[1].lower()

# Map commands to scripts
scripts = {
    'status': 'services.nylas_email.scripts.sync_emails_simple',
    'sync': 'services.nylas_email.scripts.sync_emails_simple',
    'webhook': 'services.nylas_email.scripts.setup_email_webhook',
    'test': 'services.nylas_email.tests.test_email_sync_simple',
    'manage': 'services.nylas_email.scripts.manage_email_sync'
}

if command == 'status':
    # Add --status flag for status command
    sys.argv = [sys.argv[0], '--status']
elif command == 'webhook':
    # Remove the 'webhook' argument
    sys.argv.pop(1)
elif command == 'manage':
    # Pass through all arguments after 'manage'
    sys.argv = [sys.argv[0]] + sys.argv[2:]

# Run the appropriate script
if command in scripts:
    module = scripts[command]
    exec(f"from {module} import main; main()" if command != 'test' else f"import {module}")
else:
    print(f"Unknown command: {command}")
    print("Available commands: status, sync, webhook, test, manage")
    sys.exit(1)