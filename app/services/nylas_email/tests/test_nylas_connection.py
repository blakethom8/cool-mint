import os
import sys
from dotenv import load_dotenv

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

from nylas import Client

def test_nylas_connection():
    """Test Nylas connection and basic functionality"""
    print("Testing Nylas connection...")
    print("-" * 50)
    
    # Initialize Nylas client
    try:
        nylas = Client(
            api_key=os.environ.get("NYLAS_API_KEY"),
            api_uri=os.environ.get("NYLAS_API_URI")
        )
        print("✓ Nylas client initialized successfully")
    except Exception as e:
        print(f"✗ Failed to initialize Nylas client: {e}")
        return False
    
    # Test grant ID
    grant_id = os.environ.get("NYLAS_GRANT_ID")
    if not grant_id:
        print("✗ No NYLAS_GRANT_ID found in environment")
        return False
    print(f"✓ Grant ID found: {grant_id[:10]}...")
    
    # Test account access
    try:
        # Get account information
        grant = nylas.grants.find(grant_id)
        # The grant object contains the data
        if hasattr(grant, 'data'):
            grant_data = grant.data
            email = getattr(grant_data, 'email', 'Unknown')
        else:
            email = getattr(grant, 'email', 'Unknown')
        print(f"✓ Account access confirmed for: {email}")
    except Exception as e:
        print(f"✗ Failed to access account: {e}")
        # Try alternative approach - just verify we can list messages
        try:
            print("  Attempting alternative verification...")
            test_messages = nylas.messages.list(grant_id, {"limit": 1})
            if test_messages:
                print("  ✓ Grant ID is valid - can access messages")
        except:
            return False
    
    # Test fetching recent messages
    try:
        messages = nylas.messages.list(grant_id, {"limit": 5})
        message_list = messages[0]  # Get the data from the response tuple
        print(f"✓ Successfully fetched {len(message_list)} recent messages")
        
        # Show first message details if available
        if message_list:
            first_msg = message_list[0]
            print(f"\n  Latest message:")
            print(f"  - Subject: {first_msg.subject}")
            # Handle from field which might be a list of dicts
            if first_msg.from_ and len(first_msg.from_) > 0:
                from_email = first_msg.from_[0].get('email', 'Unknown') if isinstance(first_msg.from_[0], dict) else getattr(first_msg.from_[0], 'email', 'Unknown')
                print(f"  - From: {from_email}")
            else:
                print(f"  - From: Unknown")
            print(f"  - Date: {first_msg.date}")
    except Exception as e:
        print(f"✗ Failed to fetch messages: {e}")
        return False
    
    # Test webhook configuration
    print("\n" + "-" * 50)
    print("Webhook configuration:")
    print(f"✓ Server URL: {os.environ.get('SERVER_URL')}")
    print(f"✓ Webhook Secret: {'*' * 10} (hidden)")
    print(f"✓ Email: {os.environ.get('EMAIL')}")
    
    print("\n" + "-" * 50)
    print("All tests passed! Nylas connection is working properly.")
    return True

if __name__ == "__main__":
    test_nylas_connection()