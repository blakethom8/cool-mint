from datetime import datetime
import sys
import os
from typing import Dict, List

# Add the project root to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
if project_root not in sys.path:
    sys.path.append(project_root)

from app.services.salesforce_files.salesforce_service import ReadOnlySalesforceService


def print_contact_summary(contacts: List[Dict]) -> None:
    """Print a summary of contact data."""
    print(f"\nFound {len(contacts)} contacts")
    if contacts:
        print("\nSample fields available:")
        # Get fields from first contact
        fields = list(contacts[0].keys())
        print(", ".join(fields))


def test_contact_queries():
    """Test various contact queries and data exploration."""
    print(f"\nStarting Salesforce Contact query test at {datetime.now()}")
    print("-" * 50)

    try:
        # Initialize the service
        print("Initializing ReadOnlySalesforceService...")
        sf_service = ReadOnlySalesforceService()

        # Test 1: Get available fields for Contact object
        print("\nTest 1: Getting Contact object metadata...")
        contact_metadata = sf_service.describe_object("Contact")
        print(
            f"✓ Contact object has {len(contact_metadata['fields'])} fields available"
        )

        # Print some important field names for reference
        standard_fields = [
            f["name"]
            for f in contact_metadata["fields"]
            if not f["custom"] and f["createable"]
        ]
        print("Standard fields include:", ", ".join(standard_fields[:10]))

        # Test 2: Basic Contact Query
        print("\nTest 2: Basic Contact query...")
        basic_query = """
            SELECT Id, FirstName, LastName, Email, Phone 
            FROM Contact 
            LIMIT 5
        """
        contacts = sf_service.query(basic_query)
        print_contact_summary(contacts)

        # Test 3: More Complex Query
        print("\nTest 3: Complex Contact query with relationships...")
        complex_query = """
            SELECT 
                Id, FirstName, LastName, Email,
                Account.Name, Account.Industry,
                Owner.Name
            FROM Contact 
            WHERE Email != NULL 
            ORDER BY CreatedDate DESC
            LIMIT 5
        """
        contacts_with_accounts = sf_service.query(complex_query)
        print_contact_summary(contacts_with_accounts)

        # Test 4: Try to execute an invalid query (should fail safely)
        print("\nTest 4: Testing query validation...")
        try:
            invalid_query = "UPDATE Contact SET FirstName = 'Test'"
            sf_service.query(invalid_query)
            print("❌ ERROR: Update query should have been blocked")
        except ValueError as e:
            print(f"✓ Successfully blocked invalid query: {str(e)}")

        # Test 5: Check API Usage
        print("\nTest 5: Checking API usage...")
        usage_report = sf_service.get_usage_report()
        limits = sf_service.get_api_limits()

        print(f"Today's API calls: {usage_report.get('total_calls', 0)}")
        if "DailyApiRequests" in limits:
            remaining = limits["DailyApiRequests"].get("Remaining", 0)
            maximum = limits["DailyApiRequests"].get("Max", 0)
            print(f"API Calls remaining: {remaining}/{maximum}")

        print("\n✓ All tests completed successfully!")
        print("-" * 50)
        return True

    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        print("-" * 50)
        return False


if __name__ == "__main__":
    success = test_contact_queries()
    sys.exit(0 if success else 1)
