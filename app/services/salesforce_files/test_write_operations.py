import sys
import os
from datetime import datetime

# Add the project root to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
if project_root not in sys.path:
    sys.path.append(project_root)

from app.services.salesforce_files.salesforce_service import ReadOnlySalesforceService


def test_blocked_write_operations():
    """Test that write operations are properly blocked."""
    print(f"\nStarting Salesforce write operation test at {datetime.now()}")
    print("-" * 50)

    try:
        # Initialize the service
        print("Initializing ReadOnlySalesforceService...")
        sf_service = ReadOnlySalesforceService()

        # Test 1: Attempt to create a contact via SOQL
        print("\nTest 1: Attempting to create contact via SOQL...")
        try:
            create_query = """
                INSERT INTO Contact (FirstName, LastName, Email)
                VALUES ('Test', 'Contact', 'test@example.com')
            """
            sf_service.query(create_query)
            print("❌ ERROR: Insert query should have been blocked")
        except ValueError as e:
            print(f"✓ Successfully blocked INSERT query: {str(e)}")

        # Test 2: Attempt to create a contact via direct object access
        print("\nTest 2: Attempting to create contact via direct access...")
        try:
            # This should fail because the method doesn't exist
            contact_data = {
                "FirstName": "Test",
                "LastName": "Contact",
                "Email": "test@example.com",
            }
            # Attempt to access a create method (which shouldn't exist)
            if hasattr(sf_service, "create"):
                sf_service.create("Contact", contact_data)
                print("❌ ERROR: Create operation should not be available")
            else:
                print("✓ Create method is not available on service")
        except AttributeError as e:
            print(f"✓ Successfully blocked direct create attempt: {str(e)}")

    except Exception as e:
        print(f"\n❌ Unexpected error during testing: {str(e)}")
        print("-" * 50)
        return False


if __name__ == "__main__":
    success = test_blocked_write_operations()
    sys.exit(0 if success else 1)
