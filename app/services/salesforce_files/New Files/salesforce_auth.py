import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class SalesforceAuth:
    def __init__(self):
        self.client_id = os.getenv('SALESFORCE_CLIENT_ID')
        self.client_secret = os.getenv('SALESFORCE_CLIENT_SECRET')
        self.username = os.getenv('SALESFORCE_USERNAME')
        self.password = os.getenv('SALESFORCE_PASSWORD')
        self.login_url = os.getenv('SALESFORCE_LOGIN_URL')
        self.access_token = None
        self.instance_url = None

    def authenticate(self):
        """Authenticate with Salesforce and get access token"""
        payload = {
            "grant_type": "password",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "username": self.username,
            "password": self.password
        }

        try:
            response = requests.post(self.login_url, data=payload)
            response.raise_for_status()
            token_data = response.json()
            self.access_token = token_data["access_token"]
            self.instance_url = token_data["instance_url"]
            print("Successfully authenticated with Salesforce")
            return True
        except requests.exceptions.RequestException as e:
            print(f"Authentication failed: {str(e)}")
            return False

    def get_auth_headers(self):
        """Get the authorization headers for API calls"""
        if not self.access_token:
            return None
        
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

    def get_instance_url(self):
        """Get the Salesforce instance URL"""
        return self.instance_url 