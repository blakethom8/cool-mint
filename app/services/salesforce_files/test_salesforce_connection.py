import sys
import os
from datetime import datetime

# Add the parent directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from salesforce_files.salesforce_service import SalesforceService


def test_connection():
    print(f"\nStarting Salesforce connection test at {datetime.now()}")
    print("-" * 50)

    try:
        # Initialize the service
        print("Initializing SalesforceService...")
        sf_service = SalesforceService()

        # Test 1: Basic User Query
        print("\nTest 1: Querying User information...")
        user_results = sf_service.query("SELECT Id, Name, Email FROM User LIMIT 1")
        if user_results:
            print("✓ Successfully queried User data")
            print(
                f"  Found user: {user_results[0].get('Name')} ({user_results[0].get('Email')})"
            )

        # Test 2: Account Query
        print("\nTest 2: Querying Account information...")
        account_results = sf_service.query("SELECT Id, Name FROM Account LIMIT 3")
        if account_results:
            print("✓ Successfully queried Account data")
            print(f"  Found {len(account_results)} accounts")
            for account in account_results:
                print(f"  - {account.get('Name')}")

        # Test 3: Get specific object
        print("\nTest 3: Testing object retrieval...")
        if user_results:  # Use the ID from our first query
            user_id = user_results[0]["Id"]
            user_detail = sf_service.get_object("User", user_id)
            print("✓ Successfully retrieved User object details")
            print(f"  User Name: {user_detail.get('Name')}")

        print("\n✓ All tests completed successfully!")
        print("-" * 50)
        return True

    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        print("-" * 50)
        return False


if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
