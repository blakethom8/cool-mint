import os
import requests
import json
from datetime import datetime
from dotenv import load_dotenv
from salesforce_auth import SalesforceAuth

# Load environment variables
load_dotenv()

class SalesforceAPI:
    def __init__(self):
        self.auth = SalesforceAuth()
        self.instance_url = None

    def authenticate(self):
        """Authenticate with Salesforce"""
        if self.auth.authenticate():
            self.instance_url = self.auth.get_instance_url()
            return True
        return False

    def get_report_data(self, report_id):
        """Fetch data from a Salesforce report"""
        headers = self.auth.get_auth_headers()
        if not headers:
            print("Not authenticated. Please authenticate first.")
            return None

        report_url = f"{self.instance_url}/services/data/v61.0/analytics/reports/{report_id}"

        try:
            response = requests.get(report_url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch report data: {str(e)}")
            return None

    def process_report_data(self, report_data):
        """Process and format the report data"""
        if not report_data:
            return None

        fact_map = report_data.get("factMap", {})
        groupings = report_data.get("groupingsDown", {}).get("groupings", [])
        report_metadata = report_data.get("reportMetadata", {})
        report_name = report_metadata.get("name", "Unknown Report")

        processed_data = {
            "report_name": report_name,
            "total_calls": 0,
            "completed_calls": 0,
            "calls": []
        }

        for grouping in groupings:
            key = grouping["key"]
            data = fact_map.get(f"{key}!T", {}).get("rows", [])
            for row in data:
                cells = row["dataCells"]
                call_data = {
                    "subject": cells[0]["label"],
                    "date": cells[1]["label"],
                    "status": cells[2]["label"],
                    "owner": cells[3]["label"]
                }
                processed_data["calls"].append(call_data)
                processed_data["total_calls"] += 1
                if call_data["status"] == "Completed":
                    processed_data["completed_calls"] += 1

        return processed_data

    def save_report_summary(self, processed_data, filename="sales_calls_summary.txt"):
        """Save the processed report data to a file"""
        if not processed_data:
            return False

        summary = f"""Sales Calls Summary Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Report: {processed_data['report_name']}

Summary:
- Total Calls: {processed_data['total_calls']}
- Completed Calls: {processed_data['completed_calls']}
- Pending Calls: {processed_data['total_calls'] - processed_data['completed_calls']}

Detailed Call List:
"""

        for call in processed_data["calls"]:
            summary += f"- {call['subject']} | Date: {call['date']} | Status: {call['status']} | Owner: {call['owner']}\n"

        try:
            with open(filename, "w") as f:
                f.write(summary)
            print(f"Report saved to {filename}")
            return True
        except IOError as e:
            print(f"Failed to save report: {str(e)}")
            return False

def main():
    # Initialize the Salesforce API client
    sf_api = SalesforceAPI()
    
    # Authenticate
    if not sf_api.authenticate():
        return

    # Get the report ID from environment variables
    report_id = os.getenv('SALESFORCE_REPORT_ID')
    if not report_id:
        print("No report ID provided in environment variables")
        return

    # Fetch and process the report data
    report_data = sf_api.get_report_data(report_id)
    if report_data:
        processed_data = sf_api.process_report_data(report_data)
        if processed_data:
            sf_api.save_report_summary(processed_data)

if __name__ == "__main__":
    main() 