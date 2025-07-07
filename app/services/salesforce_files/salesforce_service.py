from typing import Any, Dict, List, Optional
from simple_salesforce import Salesforce
from pydantic import BaseModel, Field
import os
from dotenv import load_dotenv
from .salesforce_monitoring import SalesforceMonitoring

load_dotenv()


class SalesforceConfig(BaseModel):
    """Configuration for Salesforce connection."""

    username: str = Field(..., description="Salesforce username")
    password: str = Field(..., description="Salesforce password")
    security_token: str = Field(..., description="Salesforce security token")
    domain: str = Field(
        default="login",
        description="Salesforce domain (e.g., 'login' for production, 'test' for sandbox)",
    )


class ReadOnlySalesforceService:
    """Service class for read-only Salesforce operations.

    This class explicitly defines only the read operations that are allowed.
    Any other Salesforce operations are not exposed and therefore cannot be accidentally used.
    """

    def __init__(self, config: Optional[SalesforceConfig] = None):
        """Initialize read-only Salesforce service."""
        if config is None:
            config = SalesforceConfig(
                username=os.getenv("SALESFORCE_USERNAME", ""),
                password=os.getenv("SALESFORCE_PASSWORD", ""),
                security_token=os.getenv("SALESFORCE_SECURITY_TOKEN", ""),
                domain=os.getenv("SALESFORCE_DOMAIN", "login"),
            )

        # Internal Salesforce client - not exposed directly
        self._sf = Salesforce(
            username=config.username,
            password=config.password,
            security_token=config.security_token,
            domain=config.domain,
        )

        # Initialize monitoring
        self.monitoring = SalesforceMonitoring()

        # Check API limits on startup
        self._check_api_limits()

    def _check_api_limits(self):
        """Check current API usage limits."""
        limits = self._sf.limits()
        self.monitoring.check_api_limits(limits)

    def query(self, soql_query: str) -> List[Dict[str, Any]]:
        """
        Execute a read-only SOQL query and return results.

        Args:
            soql_query: SOQL query string (must be SELECT only)

        Raises:
            ValueError: If query contains any modification operations
        """
        # Validate query is read-only
        query_lower = soql_query.lower().strip()
        if not query_lower.startswith("select "):
            raise ValueError("Only SELECT queries are allowed")

        # Check for any modification operations at the start of the query
        # This avoids false positives from field names or related objects
        query_parts = query_lower.split()
        if any(
            query_parts[0] == keyword
            for keyword in ["update", "delete", "insert", "upsert", "merge"]
        ):
            raise ValueError("Only SELECT queries are allowed")

        try:
            # Log the API call
            self.monitoring.log_api_call("query", {"soql": soql_query})

            # Check limits before making call
            self._check_api_limits()

            result = self._sf.query(soql_query)
            return result.get("records", [])
        except Exception as e:
            raise Exception(f"Error executing Salesforce query: {str(e)}")

    def get_object(self, object_name: str, record_id: str) -> Dict[str, Any]:
        """
        Retrieve a specific Salesforce object by ID (read-only).

        Args:
            object_name: Name of the Salesforce object (e.g., 'Contact', 'Account')
            record_id: Salesforce record ID
        """
        try:
            # Log the API call
            self.monitoring.log_api_call(
                "get_object", {"object": object_name, "id": record_id}
            )

            # Check limits before making call
            self._check_api_limits()

            # Use SOQL instead of direct object access to ensure read-only
            query = f"SELECT * FROM {object_name} WHERE Id = '{record_id}' LIMIT 1"
            results = self.query(query)

            if not results:
                return {}
            return results[0]
        except Exception as e:
            raise Exception(f"Error retrieving Salesforce object: {str(e)}")

    def describe_object(self, object_name: str) -> Dict[str, Any]:
        """
        Get metadata about a Salesforce object (read-only).

        Args:
            object_name: Name of the Salesforce object to describe
        """
        try:
            # Log the API call
            self.monitoring.log_api_call("describe_object", {"object": object_name})

            # Check limits before making call
            self._check_api_limits()

            # Get the object handler but only use its describe method
            sf_object = getattr(self._sf, object_name)
            return sf_object.describe()
        except Exception as e:
            raise Exception(f"Error describing Salesforce object: {str(e)}")

    def get_api_limits(self) -> Dict[str, Any]:
        """Get current API usage and limits."""
        limits = self._sf.limits()
        self.monitoring.log_api_call("get_limits", limits)
        return limits

    def get_usage_report(self, date: str = None) -> Dict[str, Any]:
        """Get API usage report for a specific date."""
        return self.monitoring.get_usage_report(date)

    def list_available_objects(self) -> List[str]:
        """
        Get list of available Salesforce objects (read-only).
        """
        try:
            # Log the API call
            self.monitoring.log_api_call("list_objects", {})

            # Check limits before making call
            self._check_api_limits()

            # Get global describe
            result = self._sf.describe()
            return [obj["name"] for obj in result["sobjects"]]
        except Exception as e:
            raise Exception(f"Error listing Salesforce objects: {str(e)}")
