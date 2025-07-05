import requests
import json
import time
import csv
import io
from typing import Dict, List, Optional, Any
from datetime import datetime
import os
from dotenv import load_dotenv
from .salesforce_monitoring import SalesforceMonitoring

load_dotenv()


class BulkSalesforceService:
    """Service class for Salesforce Bulk API operations.

    This class is designed for large-scale data extraction using the Salesforce Bulk API 2.0.
    It's optimized for handling hundreds of thousands of records efficiently.
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
        """
        Initialize Salesforce Bulk API client

        Args:
            username: Salesforce username (defaults to env var)
            password: Salesforce password (defaults to env var)
            security_token: Salesforce security token (defaults to env var)
            client_id: Salesforce connected app client ID (defaults to env var)
            client_secret: Salesforce connected app client secret (defaults to env var)
            sandbox: True if using sandbox environment
        """
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

            print("✅ Successfully authenticated with Salesforce Bulk API")
            self.monitoring.log_api_call("bulk_authenticate", {"success": True})
            return True

        except Exception as e:
            print(f"❌ Bulk API authentication failed: {str(e)}")
            self.monitoring.log_api_call(
                "bulk_authenticate", {"success": False, "error": str(e)}
            )
            return False

    def create_bulk_query_job(
        self, query: str, object_name: str = "Contact"
    ) -> Optional[str]:
        """
        Create a bulk query job

        Args:
            query: SOQL query to execute
            object_name: Salesforce object name (defaults to Contact)

        Returns:
            Job ID if successful, None otherwise
        """
        try:
            job_data = {
                "operation": "query",
                "query": query,
                "contentType": "CSV",
                "lineEnding": "LF",
            }

            url = f"{self.instance_url}/services/data/{self.api_version}/jobs/query"
            response = requests.post(url, headers=self.headers, json=job_data)
            response.raise_for_status()

            job_info = response.json()
            job_id = job_info["id"]

            print(f"✅ Created bulk query job: {job_id}")
            self.monitoring.log_api_call(
                "bulk_create_job", {"job_id": job_id, "object": object_name}
            )
            return job_id

        except Exception as e:
            print(f"❌ Failed to create bulk query job: {str(e)}")
            self.monitoring.log_api_call(
                "bulk_create_job", {"success": False, "error": str(e)}
            )
            return None

    def check_job_status(self, job_id: str) -> Dict:
        """
        Check the status of a bulk job

        Args:
            job_id: The job ID to check

        Returns:
            Job status information
        """
        try:
            url = f"{self.instance_url}/services/data/{self.api_version}/jobs/query/{job_id}"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()

            return response.json()

        except Exception as e:
            print(f"❌ Failed to check job status: {str(e)}")
            return {}

    def wait_for_job_completion(self, job_id: str, max_wait_time: int = 3600) -> bool:
        """
        Wait for a bulk job to complete

        Args:
            job_id: The job ID to monitor
            max_wait_time: Maximum time to wait in seconds

        Returns:
            True if job completed successfully, False otherwise
        """
        start_time = time.time()
        last_update = 0

        while time.time() - start_time < max_wait_time:
            job_status = self.check_job_status(job_id)

            if not job_status:
                return False

            state = job_status.get("state", "")
            records_processed = job_status.get("numberRecordsProcessed", 0)

            # Only print updates every 30 seconds or when state changes
            if time.time() - last_update > 30 or records_processed != last_update:
                print(
                    f"📊 Job {job_id} - State: {state}, Records Processed: {records_processed:,}"
                )
                last_update = time.time()

            if state == "JobComplete":
                total_records = job_status.get("numberRecordsProcessed", 0)
                print(
                    f"✅ Job {job_id} completed successfully! Total records: {total_records:,}"
                )
                self.monitoring.log_api_call(
                    "bulk_job_complete",
                    {
                        "job_id": job_id,
                        "total_records": total_records,
                        "duration": time.time() - start_time,
                    },
                )
                return True
            elif state == "Failed":
                error_msg = job_status.get("stateMessage", "Unknown error")
                print(f"❌ Job {job_id} failed: {error_msg}")
                self.monitoring.log_api_call(
                    "bulk_job_failed", {"job_id": job_id, "error": error_msg}
                )
                return False
            elif state == "Aborted":
                print(f"❌ Job {job_id} was aborted!")
                self.monitoring.log_api_call("bulk_job_aborted", {"job_id": job_id})
                return False

            # Wait before checking again
            time.sleep(10)

        print(f"⏰ Job {job_id} did not complete within {max_wait_time} seconds")
        self.monitoring.log_api_call(
            "bulk_job_timeout", {"job_id": job_id, "timeout": max_wait_time}
        )
        return False

    def get_job_results(self, job_id: str) -> str:
        """
        Get the results of a completed bulk query job as CSV string

        Args:
            job_id: The completed job ID

        Returns:
            CSV data as string
        """
        try:
            url = f"{self.instance_url}/services/data/{self.api_version}/jobs/query/{job_id}/results"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()

            # The response contains CSV data
            csv_data = response.text
            self.monitoring.log_api_call(
                "bulk_get_results", {"job_id": job_id, "data_size": len(csv_data)}
            )
            return csv_data

        except Exception as e:
            print(f"❌ Failed to get job results: {str(e)}")
            self.monitoring.log_api_call(
                "bulk_get_results", {"success": False, "error": str(e)}
            )
            return ""

    def parse_csv_results(self, csv_data: str) -> List[Dict[str, Any]]:
        """
        Parse CSV results into list of dictionaries

        Args:
            csv_data: Raw CSV data string

        Returns:
            List of dictionaries representing records
        """
        try:
            # Use CSV reader to parse the data
            csv_reader = csv.DictReader(io.StringIO(csv_data))
            records = []

            for row in csv_reader:
                # Convert empty strings to None for proper database handling
                processed_row = {}
                for key, value in row.items():
                    if value == "" or value == "null":
                        processed_row[key] = None
                    else:
                        processed_row[key] = value
                records.append(processed_row)

            print(f"✅ Parsed {len(records):,} records from CSV")
            return records

        except Exception as e:
            print(f"❌ Failed to parse CSV results: {str(e)}")
            return []

    def execute_bulk_query(
        self, query: str, object_name: str = "Contact"
    ) -> List[Dict[str, Any]]:
        """
        Execute a complete bulk query operation

        Args:
            query: SOQL query to execute
            object_name: Salesforce object name

        Returns:
            List of dictionaries representing records
        """
        print(f"🚀 Starting bulk query for {object_name}")
        print(f"📋 Query: {query[:100]}...")

        # Step 1: Authenticate
        if not self.authenticate():
            return []

        # Step 2: Create bulk query job
        job_id = self.create_bulk_query_job(query, object_name)
        if not job_id:
            return []

        # Step 3: Wait for job completion
        if not self.wait_for_job_completion(job_id):
            return []

        # Step 4: Get results
        print(f"📥 Downloading results...")
        csv_data = self.get_job_results(job_id)

        if not csv_data:
            print("❌ No data received from job")
            return []

        # Step 5: Parse results
        records = self.parse_csv_results(csv_data)

        print(
            f"✅ Bulk query completed successfully! Retrieved {len(records):,} records"
        )
        return records

    def get_api_limits(self) -> Dict[str, Any]:
        """Get current API usage and limits (if available)"""
        try:
            if not self.session_id:
                return {}

            url = f"{self.instance_url}/services/data/{self.api_version}/limits"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()

            limits = response.json()
            self.monitoring.log_api_call("bulk_get_limits", limits)
            return limits

        except Exception as e:
            print(f"❌ Failed to get API limits: {str(e)}")
            return {}
