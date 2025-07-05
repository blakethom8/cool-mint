# Salesforce Call Data Analyzer

This project fetches call data from Salesforce and processes it for analysis. It uses the Salesforce REST API to retrieve data from reports and saves the processed information locally.

## Project Structure

The project is organized into the following components:

- `salesforce_auth.py`: Handles Salesforce authentication and token management
- `salesforce_api.py`: Manages API calls and data processing
- `requirements.txt`: Lists project dependencies
- `.env`: Configuration file for credentials (not tracked in git)
- `setup_venv.ps1`: PowerShell script for virtual environment setup

## Setup Instructions

### Setting up the Virtual Environment

1. Using the setup script (recommended):
   ```powershell
   # Run the setup script
   .\setup_venv.ps1
   ```

   This script will:
   - Create a virtual environment if it doesn't exist
   - Activate the virtual environment
   - Install all required packages
   - Verify the installation

2. Manual setup:
   ```bash
   # Create virtual environment
   python -m venv venv
   
   # Activate virtual environment
   # On Windows:
   .\venv\Scripts\activate
   # On Unix/MacOS:
   source venv/bin/activate
   
   # Install requirements
   pip install -r requirements.txt
   ```

### Setting up Cursor IDE

To ensure Cursor IDE uses the virtual environment:

1. Open Cursor IDE
2. Open the integrated terminal (if not already open)
3. Run the setup script or manually activate the virtual environment
4. Verify the virtual environment is active by checking the terminal prompt (should show `(venv)`)

### Environment Variables

Create a `.env` file in the project root directory with the following variables:
```
SALESFORCE_CLIENT_ID=your_consumer_key_here
SALESFORCE_CLIENT_SECRET=your_consumer_secret_here
SALESFORCE_USERNAME=your_username_here
SALESFORCE_PASSWORD=your_password_plus_security_token_here
SALESFORCE_LOGIN_URL=https://login.salesforce.com/services/oauth2/token
SALESFORCE_REPORT_ID=your_report_id_here
OPENAI_API_KEY=your_openai_api_key_here
```

Note: Replace the placeholder values with your actual Salesforce and OpenAI credentials.

## Component Details

### Authentication (`salesforce_auth.py`)
- Handles OAuth 2.0 authentication with Salesforce
- Manages access tokens and instance URLs
- Provides authentication headers for API calls

### API Integration (`salesforce_api.py`)
- Manages report data retrieval
- Processes and formats the data
- Saves summaries to local files

## Usage

Run the main script:
```bash
python salesforce_api.py
```

The script will:
1. Authenticate with Salesforce using the credentials from `.env`
2. Fetch the specified report data
3. Process and format the data
4. Save a summary to `sales_calls_summary.txt`

## Security Notes

- Never commit your `.env` file to version control
- Keep your Salesforce and OpenAI credentials secure
- The `.env` file is included in `.gitignore` to prevent accidental commits
- Access tokens are managed securely and not stored persistently

## Requirements

- Python 3.8 or higher
- Salesforce account with API access
- Connected App in Salesforce with OAuth 2.0 enabled
- OpenAI API key

## Dependencies

- requests==2.32.3
- python-dotenv==1.1.0
- openai==1.84.0

## Error Handling

The application includes error handling for:
- Authentication failures
- API request failures
- File I/O operations
- Missing environment variables

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request 