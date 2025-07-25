import os
import sys
from dotenv import load_dotenv

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

from nylas import Client
from nylas.models.webhooks import CreateWebhookRequest, WebhookTriggers

def list_existing_webhooks():
    """List all existing webhooks"""
    nylas = Client(
        api_key=os.environ.get("NYLAS_API_KEY"),
        api_uri=os.environ.get("NYLAS_API_URI"),
    )
    
    print("Existing webhooks:")
    print("-" * 50)
    
    try:
        webhooks = nylas.webhooks.list()
        if webhooks.data:
            for webhook in webhooks.data:
                print(f"ID: {webhook.id}")
                print(f"URL: {webhook.webhook_url}")
                print(f"Triggers: {webhook.trigger_types}")
                print(f"Status: {webhook.status}")
                print("-" * 50)
        else:
            print("No webhooks found")
    except Exception as e:
        print(f"Error listing webhooks: {e}")

def setup_email_webhook():
    """Setup Nylas webhook for email events"""
    nylas = Client(
        api_key=os.environ.get("NYLAS_API_KEY"),
        api_uri=os.environ.get("NYLAS_API_URI"),
    )
    
    # Check if SERVER_URL is configured
    server_url = os.environ.get("SERVER_URL")
    if not server_url:
        print("ERROR: SERVER_URL not configured in .env")
        print("Please run Pinggy tunnel and set SERVER_URL first")
        return
    
    # Construct webhook URL
    webhook_url = f"{server_url}/api/webhooks/nylas"
    print(f"Setting up webhook at: {webhook_url}")
    
    # Define the webhook properties
    request_body = CreateWebhookRequest(
        trigger_types=[
            WebhookTriggers.MESSAGE_CREATED,
            WebhookTriggers.MESSAGE_UPDATED,
        ],
        webhook_url=webhook_url,
        description="Email Processing Webhook",
        notification_email_addresses=[os.environ.get("EMAIL")],
    )
    
    try:
        # Create the webhook
        webhook, _, _ = nylas.webhooks.create(request_body=request_body)
        
        print("\nWebhook created successfully!")
        print(f"Webhook ID: {webhook.id}")
        print(f"Webhook Secret: {webhook.webhook_secret}")
        print("\nIMPORTANT: Add this webhook secret to your .env file:")
        print(f"WEBHOOK_SECRET={webhook.webhook_secret}")
        
    except Exception as e:
        print(f"Error creating webhook: {e}")

if __name__ == "__main__":
    print("Nylas Webhook Setup")
    print("=" * 50)
    
    # List existing webhooks
    list_existing_webhooks()
    
    # Ask if user wants to create a new webhook
    print("\nDo you want to create a new webhook? (y/n): ", end="")
    response = input().strip().lower()
    
    if response == 'y':
        setup_email_webhook()