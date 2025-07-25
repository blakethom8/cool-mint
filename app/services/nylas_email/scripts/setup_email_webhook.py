#!/usr/bin/env python3
"""
Email Webhook Setup Script

This script:
1. Starts a Pinggy tunnel
2. Configures Nylas webhooks
3. Manages webhook lifecycle
"""

import os
import sys
import time
import signal
import subprocess
import argparse
from typing import Optional

# Add the app directory to Python path
app_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, app_dir)

from dotenv import load_dotenv, set_key
load_dotenv()

from nylas import Client
from nylas.models.webhooks import CreateWebhookRequest, WebhookTriggers


class WebhookManager:
    def __init__(self):
        self.nylas = Client(
            api_key=os.environ.get("NYLAS_API_KEY"),
            api_uri=os.environ.get("NYLAS_API_URI"),
        )
        self.pinggy_process = None
        self.webhook_id = None
        
    def list_webhooks(self):
        """List all existing webhooks"""
        print("\nExisting webhooks:")
        print("-" * 70)
        
        try:
            webhooks = self.nylas.webhooks.list()
            if webhooks.data:
                for webhook in webhooks.data:
                    print(f"ID: {webhook.id}")
                    print(f"URL: {webhook.webhook_url}")
                    print(f"Triggers: {webhook.trigger_types}")
                    print(f"Status: {webhook.status}")
                    print(f"Created: {webhook.created_at}")
                    print("-" * 70)
                return webhooks.data
            else:
                print("No webhooks found")
                return []
        except Exception as e:
            print(f"Error listing webhooks: {e}")
            return []
    
    def delete_webhook(self, webhook_id: str):
        """Delete a specific webhook"""
        try:
            self.nylas.webhooks.destroy(webhook_id)
            print(f"✓ Deleted webhook: {webhook_id}")
        except Exception as e:
            print(f"✗ Error deleting webhook {webhook_id}: {e}")
    
    def cleanup_old_webhooks(self, keep_url: Optional[str] = None):
        """Delete old webhooks, optionally keeping one with specific URL"""
        webhooks = self.list_webhooks()
        for webhook in webhooks:
            if keep_url and webhook.webhook_url == keep_url:
                print(f"Keeping webhook: {webhook.id}")
                continue
            self.delete_webhook(webhook.id)
    
    def start_pinggy_tunnel(self, port: int = 8080):
        """Start Pinggy tunnel and return the public URL"""
        print(f"\nStarting Pinggy tunnel on port {port}...")
        
        # Start Pinggy process
        cmd = ["ssh", "-p", "443", f"-R0:localhost:{port}", "a.pinggy.io"]
        self.pinggy_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # Wait for URL
        pinggy_url = None
        start_time = time.time()
        timeout = 30
        
        while time.time() - start_time < timeout:
            line = self.pinggy_process.stdout.readline()
            if line:
                print(f"Pinggy: {line.strip()}")
                # Look for the URL in the output
                if "https://" in line and ".a.pinggy.link" in line:
                    # Extract URL from the line
                    parts = line.split()
                    for part in parts:
                        if "https://" in part and ".a.pinggy.link" in part:
                            pinggy_url = part.strip()
                            break
                    if pinggy_url:
                        break
        
        if not pinggy_url:
            print("✗ Failed to get Pinggy URL")
            self.stop_pinggy_tunnel()
            return None
        
        print(f"✓ Pinggy tunnel started: {pinggy_url}")
        return pinggy_url
    
    def stop_pinggy_tunnel(self):
        """Stop the Pinggy tunnel"""
        if self.pinggy_process:
            print("\nStopping Pinggy tunnel...")
            self.pinggy_process.terminate()
            self.pinggy_process.wait()
            self.pinggy_process = None
            print("✓ Pinggy tunnel stopped")
    
    def create_webhook(self, webhook_url: str):
        """Create Nylas webhook"""
        print(f"\nCreating webhook at: {webhook_url}")
        
        request_body = CreateWebhookRequest(
            trigger_types=[
                WebhookTriggers.MESSAGE_CREATED,
                WebhookTriggers.MESSAGE_UPDATED,
            ],
            webhook_url=webhook_url,
            description="Email Processing Webhook (dev)",
            notification_email_addresses=[os.environ.get("EMAIL")],
        )
        
        try:
            webhook, _, _ = self.nylas.webhooks.create(request_body=request_body)
            self.webhook_id = webhook.id
            
            print("\n✓ Webhook created successfully!")
            print(f"Webhook ID: {webhook.id}")
            print(f"Webhook Secret: {webhook.webhook_secret}")
            
            # Update .env file with webhook secret
            env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
            set_key(env_path, "WEBHOOK_SECRET", webhook.webhook_secret)
            set_key(env_path, "SERVER_URL", webhook_url.replace("/api/webhooks/nylas", ""))
            
            print("\n✓ Updated .env file with webhook configuration")
            
            return webhook
            
        except Exception as e:
            print(f"✗ Error creating webhook: {e}")
            return None
    
    def run_webhook_mode(self, port: int = 8080, cleanup: bool = True):
        """Run in webhook mode with Pinggy tunnel"""
        # Clean up old webhooks if requested
        if cleanup:
            print("\nCleaning up old webhooks...")
            self.cleanup_old_webhooks()
        
        # Start Pinggy tunnel
        pinggy_url = self.start_pinggy_tunnel(port)
        if not pinggy_url:
            return
        
        # Create webhook
        webhook_url = f"{pinggy_url}/api/webhooks/nylas"
        webhook = self.create_webhook(webhook_url)
        
        if webhook:
            print("\n" + "=" * 70)
            print("WEBHOOK ACTIVE - Press Ctrl+C to stop")
            print("=" * 70)
            print(f"Pinggy URL: {pinggy_url}")
            print(f"Webhook URL: {webhook_url}")
            print(f"Local server should be running on port {port}")
            print("\nTo test: Send an email to your connected account")
            print("=" * 70)
            
            # Keep running until interrupted
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n\nShutting down...")
        
        # Cleanup
        self.stop_pinggy_tunnel()
        if self.webhook_id and cleanup:
            print("\nDeleting webhook...")
            self.delete_webhook(self.webhook_id)


def main():
    parser = argparse.ArgumentParser(description="Manage email webhooks")
    parser.add_argument(
        "--list", 
        action="store_true",
        help="List existing webhooks"
    )
    parser.add_argument(
        "--cleanup", 
        action="store_true",
        help="Delete all existing webhooks"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=8080,
        help="Local port for webhook endpoint (default: 8080)"
    )
    parser.add_argument(
        "--no-cleanup", 
        action="store_true",
        help="Don't cleanup webhooks on exit"
    )
    
    args = parser.parse_args()
    
    manager = WebhookManager()
    
    # Handle signal for clean shutdown
    def signal_handler(sig, frame):
        print("\n\nReceived interrupt signal...")
        manager.stop_pinggy_tunnel()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    if args.list:
        manager.list_webhooks()
    elif args.cleanup:
        manager.cleanup_old_webhooks()
        print("✓ All webhooks deleted")
    else:
        # Run webhook mode
        print("Starting Email Webhook Setup")
        print("=" * 70)
        manager.run_webhook_mode(
            port=args.port, 
            cleanup=not args.no_cleanup
        )


if __name__ == "__main__":
    main()