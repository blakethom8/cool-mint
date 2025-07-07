import sys
import os
from datetime import datetime

# Add the project root to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
if project_root not in sys.path:
    sys.path.append(project_root)

from app.services.salesforce_files.bulk_salesforce_service import BulkSalesforceService


def test_bulk_api():
    """Test the Bulk API connection and basic functionality."""
    print(f"\n🚀 Testing Salesforce Bulk API Connection")
    print(f"Time: {datetime.now()}")
    print("-" * 60)

    try:
        # Initialize the bulk service
        print("1. Initializing BulkSalesforceService...")
        sf_bulk = BulkSalesforceService()

        # Test authentication
        print("2. Testing authentication...")
        if sf_bulk.authenticate():
            print("✅ Authentication successful!")
        else:
            print("❌ Authentication failed!")
            return False

        # Test a simple query
        print("3. Testing simple bulk query...")
        test_query = """
            SELECT Id, FirstName, LastName, Email, Phone, CreatedDate
            FROM Contact 
            WHERE IsDeleted = FALSE 
            LIMIT 5
        """

        print(f"   Query: {test_query.strip()}")
        results = sf_bulk.execute_bulk_query(test_query)

        if results:
            print(f"✅ Query successful! Retrieved {len(results)} sample records")

            # Display sample results
            print("\n   Sample contact data:")
            for i, contact in enumerate(results[:3]):  # Show first 3
                print(
                    f"   {i + 1}. {contact.get('FirstName', 'N/A')} {contact.get('LastName', 'N/A')} ({contact.get('Email', 'No email')})"
                )

            return True
        else:
            print("❌ Query failed - no results returned")
            return False

    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        return False


def test_api_limits():
    """Test API limits checking."""
    print("\n4. Testing API limits...")

    try:
        sf_bulk = BulkSalesforceService()

        if sf_bulk.authenticate():
            limits = sf_bulk.get_api_limits()

            if limits:
                print("✅ API limits retrieved successfully!")

                # Display some key limits
                if "DailyApiRequests" in limits:
                    daily = limits["DailyApiRequests"]
                    print(
                        f"   Daily API Requests: {daily.get('Remaining', 'N/A')}/{daily.get('Max', 'N/A')} remaining"
                    )

                if "DailyBulkApiRequests" in limits:
                    bulk = limits["DailyBulkApiRequests"]
                    print(
                        f"   Daily Bulk API Requests: {bulk.get('Remaining', 'N/A')}/{bulk.get('Max', 'N/A')} remaining"
                    )

                return True
            else:
                print("⚠️  API limits not available")
                return True  # Not a failure, just not available

    except Exception as e:
        print(f"❌ API limits test failed: {str(e)}")
        return False


def estimate_sync_time():
    """Estimate how long a full sync might take."""
    print("\n5. Estimating sync time...")

    try:
        sf_bulk = BulkSalesforceService()

        if sf_bulk.authenticate():
            # Count total contacts
            count_query = """
                SELECT COUNT(Id) total_count
                FROM Contact 
                WHERE IsDeleted = FALSE
            """

            results = sf_bulk.execute_bulk_query(count_query)

            if results and results[0].get("total_count"):
                total_contacts = int(results[0]["total_count"])
                print(f"✅ Total contacts in Salesforce: {total_contacts:,}")

                # Estimate based on typical bulk API performance
                # Bulk API typically processes 2000-5000 records per minute
                estimated_minutes = total_contacts / 3000  # Conservative estimate

                print(f"   Estimated sync time: {estimated_minutes:.1f} minutes")

                if estimated_minutes > 60:
                    hours = estimated_minutes / 60
                    print(f"   That's approximately {hours:.1f} hours")

                return True
            else:
                print("❌ Could not retrieve contact count")
                return False

    except Exception as e:
        print(f"❌ Estimation failed: {str(e)}")
        return False


def main():
    """Run all tests."""
    print("🔧 SALESFORCE BULK API TEST SUITE")
    print("=" * 60)

    tests = [
        ("Bulk API Connection", test_bulk_api),
        ("API Limits", test_api_limits),
        ("Sync Time Estimation", estimate_sync_time),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {str(e)}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"TEST RESULTS: {passed} passed, {failed} failed")

    if failed == 0:
        print("✅ All tests passed! Your Bulk API setup is ready.")
        print("\nYou can now run the full sync with:")
        print(
            "python app/services/salesforce_files/production_contact_sync_bulk.py --full"
        )
    else:
        print("❌ Some tests failed. Please check your configuration.")

    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
