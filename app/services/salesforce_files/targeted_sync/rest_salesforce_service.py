import requests
import json
from typing import List, Optional, Dict, Any
from datetime import datetime
import os
from dotenv import load_dotenv

try:
    from ..salesforce_monitoring import SalesforceMonitoring
except ImportError:
    import sys
    import os

    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from salesforce_monitoring import SalesforceMonitoring

load_dotenv()


class RestSalesforceService:
    """Service class for Salesforce REST API operations.

    This class is optimized for relationship queries and small result sets,
    perfect for getting lists of IDs to feed into Bulk API operations.
    """

    def __init__(
        self,
        username: str = None,
        password: str = None,
        security_token: str = None,
        client_id: str = None,
        client_secret: str = None,
        sandbox: bool = False,
    ):
        """Initialize Salesforce REST API client"""
        self.username = username or os.getenv("SALESFORCE_USERNAME", "")
        self.password = password or os.getenv("SALESFORCE_PASSWORD", "")
        self.security_token = security_token or os.getenv(
            "SALESFORCE_SECURITY_TOKEN", ""
        )
        self.client_id = client_id or os.getenv("SALESFORCE_CLIENT_ID", "")
        self.client_secret = client_secret or os.getenv("SALESFORCE_CLIENT_SECRET", "")
        self.sandbox = sandbox or os.getenv("SALESFORCE_DOMAIN", "login") == "test"

        # Set base URLs
        if self.sandbox:
            self.login_url = "https://test.salesforce.com/services/oauth2/token"
            self.api_version = "v58.0"
        else:
            self.login_url = "https://login.salesforce.com/services/oauth2/token"
            self.api_version = "v58.0"

        self.session_id = None
        self.instance_url = None
        self.headers = None

        # Initialize monitoring
        self.monitoring = SalesforceMonitoring()

    def authenticate(self) -> bool:
        """Authenticate with Salesforce and get session token"""
        try:
            # Validate required credentials
            if not all(
                [self.username, self.password, self.client_id, self.client_secret]
            ):
                missing = []
                if not self.username:
                    missing.append("SALESFORCE_USERNAME")
                if not self.password:
                    missing.append("SALESFORCE_PASSWORD")
                if not self.client_id:
                    missing.append("SALESFORCE_CLIENT_ID")
                if not self.client_secret:
                    missing.append("SALESFORCE_CLIENT_SECRET")

                raise ValueError(
                    f"Missing required environment variables: {', '.join(missing)}"
                )

            # Use OAuth 2.0 Username-Password flow
            auth_data = {
                "grant_type": "password",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "username": self.username,
                "password": self.password + self.security_token,
            }

            # Make authentication request
            response = requests.post(self.login_url, data=auth_data)
            response.raise_for_status()

            auth_result = response.json()
            self.session_id = auth_result["access_token"]
            self.instance_url = auth_result["instance_url"]

            # Set up headers for API calls
            self.headers = {
                "Authorization": f"Bearer {self.session_id}",
                "Content-Type": "application/json",
            }

            print("✅ Successfully authenticated with Salesforce REST API")
            self.monitoring.log_api_call("rest_authenticate", {"success": True})
            return True

        except Exception as e:
            print(f"❌ REST API authentication failed: {str(e)}")
            self.monitoring.log_api_call(
                "rest_authenticate", {"success": False, "error": str(e)}
            )
            return False

    def execute_soql_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute a SOQL query and return all results (handles pagination automatically)"""
        if not self.session_id:
            if not self.authenticate():
                return []

        try:
            all_records = []
            next_url = None

            # Initial query
            url = f"{self.instance_url}/services/data/{self.api_version}/query/"
            params = {"q": query}

            while True:
                if next_url:
                    # Use the next records URL for pagination
                    response = requests.get(next_url, headers=self.headers)
                else:
                    # Initial query
                    response = requests.get(url, headers=self.headers, params=params)

                response.raise_for_status()
                result = response.json()

                # Add records to our collection
                all_records.extend(result.get("records", []))

                # Check if there are more records
                if result.get("done", True):
                    break

                # Get the next batch URL
                next_url = f"{self.instance_url}{result.get('nextRecordsUrl', '')}"

                print(f"📄 Retrieved {len(all_records):,} records so far...")

            print(f"✅ Query completed: {len(all_records):,} total records")
            self.monitoring.log_api_call(
                "rest_query",
                {
                    "query": query[:100] + "..." if len(query) > 100 else query,
                    "records_count": len(all_records),
                },
            )

            return all_records

        except Exception as e:
            print(f"❌ REST API query failed: {str(e)}")
            self.monitoring.log_api_call(
                "rest_query", {"success": False, "error": str(e)}
            )
            return []

    def get_contact_ids_with_activities(
        self, modified_since: Optional[datetime] = None
    ) -> List[str]:
        """Get unique Contact IDs that have activities logged against them via TaskWhoRelation"""
        try:
            print("🔍 Getting Contact IDs from TaskWhoRelation...")

            # Build query for contacts in TaskWhoRelation using GROUP BY
            query = "SELECT RelationId FROM TaskWhoRelation WHERE RelationId != null"

            # Add time filter if specified - Note: TaskWhoRelation doesn't have LastModifiedDate
            # We'll filter by the related Task's LastModifiedDate if needed
            if modified_since:
                # Use relationship query to Task
                query += f" AND Task.LastModifiedDate >= {modified_since.isoformat()}Z"

            query += " GROUP BY RelationId ORDER BY RelationId"

            print(f"📋 Executing TaskWhoRelation query: {query}")
            results = self.execute_soql_query(query)

            if not results:
                print("⚠️  No contacts with activities found in TaskWhoRelation")
                return []

            # Extract unique contact IDs
            contact_ids = []
            for record in results:
                relation_id = record.get("RelationId")
                if relation_id and relation_id.startswith(
                    "003"
                ):  # Ensure it's a Contact ID
                    contact_ids.append(relation_id)

            # Remove duplicates and sort
            unique_contact_ids = sorted(list(set(contact_ids)))

            print(
                f"✅ Found {len(unique_contact_ids):,} unique contacts with activities from TaskWhoRelation"
            )
            return unique_contact_ids

        except Exception as e:
            print(f"❌ Error getting contact IDs from TaskWhoRelation: {str(e)}")
            return []

    def get_contact_ids_with_events(
        self, modified_since: Optional[datetime] = None
    ) -> List[str]:
        """Get unique Contact IDs that have Event activities logged against them"""
        try:
            print("🔍 Getting Contact IDs with Event activities...")

            # Build query for contacts with events
            query = "SELECT DISTINCT WhoId FROM Event WHERE WhoId != null AND IsDeleted = FALSE AND WhoId LIKE '003%'"

            # Add time filter if specified
            if modified_since:
                query += f" AND LastModifiedDate >= {modified_since.isoformat()}Z"

            query += " ORDER BY WhoId"

            print(f"📋 Executing query: {query}")
            results = self.execute_soql_query(query)

            if not results:
                print("⚠️  No contacts with events found")
                return []

            # Extract unique contact IDs
            contact_ids = []
            for record in results:
                who_id = record.get("WhoId")
                if who_id and who_id.startswith("003"):  # Ensure it's a Contact ID
                    contact_ids.append(who_id)

            # Remove duplicates and sort
            unique_contact_ids = sorted(list(set(contact_ids)))

            print(f"✅ Found {len(unique_contact_ids):,} unique contacts with events")
            return unique_contact_ids

        except Exception as e:
            print(f"❌ Error getting contact IDs with events: {str(e)}")
            return []

    def get_all_contact_ids_with_activities(
        self, modified_since: Optional[datetime] = None
    ) -> List[str]:
        """Get all unique Contact IDs that have activities logged against them via TaskWhoRelation"""
        try:
            print("🎯 Getting all Contact IDs with activities from TaskWhoRelation...")

            # Get contacts from TaskWhoRelation (comprehensive list)
            contact_ids = self.get_contact_ids_with_activities(modified_since)

            print(f"📊 Summary:")
            print(f"  - Contacts from TaskWhoRelation: {len(contact_ids):,}")
            print(f"  - Using TaskWhoRelation for complete activity coverage")

            return contact_ids

        except Exception as e:
            print(f"❌ Error getting contact IDs from TaskWhoRelation: {str(e)}")
            return []

    def get_activity_counts(self) -> Dict[str, int]:
        """Get statistics about activities in the Salesforce org via TaskWhoRelation"""
        try:
            print("📊 Getting activity statistics from TaskWhoRelation...")

            # Count total task-contact relationships
            task_relations_query = (
                "SELECT COUNT(Id) FROM TaskWhoRelation WHERE RelationId != null"
            )
            relations_results = self.execute_soql_query(task_relations_query)
            total_relations = (
                relations_results[0].get("expr0", 0) if relations_results else 0
            )

            # Get unique contacts using GROUP BY approach (more compatible than COUNT(DISTINCT))
            unique_contacts_query = "SELECT RelationId FROM TaskWhoRelation WHERE RelationId != null GROUP BY RelationId"
            contacts_results = self.execute_soql_query(unique_contacts_query)
            unique_contacts = len(contacts_results) if contacts_results else 0

            # Get unique tasks using GROUP BY approach
            unique_tasks_query = "SELECT TaskId FROM TaskWhoRelation WHERE TaskId != null GROUP BY TaskId"
            tasks_results = self.execute_soql_query(unique_tasks_query)
            unique_tasks = len(tasks_results) if tasks_results else 0

            stats = {
                "total_task_relations": total_relations,
                "unique_contacts_with_activities": unique_contacts,
                "unique_tasks": unique_tasks,
                "total_activities": total_relations,  # Each relation represents an activity connection
            }

            print(f"📈 TaskWhoRelation Statistics:")
            print(
                f"  - Total Task-Contact Relations: {stats['total_task_relations']:,}"
            )
            print(
                f"  - Unique Contacts with Activities: {stats['unique_contacts_with_activities']:,}"
            )
            print(f"  - Unique Tasks: {stats['unique_tasks']:,}")
            print(f"  - Total Activity Connections: {stats['total_activities']:,}")

            return stats

        except Exception as e:
            print(f"❌ Error getting TaskWhoRelation statistics: {str(e)}")
            return {
                "total_task_relations": 0,
                "unique_contacts_with_activities": 0,
                "unique_tasks": 0,
                "total_activities": 0,
            }

    def test_connection(self) -> bool:
        """Test the REST API connection with a simple query"""
        try:
            print("🔧 Testing REST API connection...")

            if not self.authenticate():
                return False

            # Test with a simple query
            test_query = "SELECT Id, FirstName, LastName FROM Contact LIMIT 5"
            results = self.execute_soql_query(test_query)

            if results:
                print(
                    f"✅ REST API test successful! Retrieved {len(results)} sample contacts"
                )
                return True
            else:
                print("❌ REST API test failed - no results returned")
                return False

        except Exception as e:
            print(f"❌ REST API test failed: {str(e)}")
            return False
