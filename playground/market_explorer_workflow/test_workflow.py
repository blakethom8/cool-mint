import sys
import os
from pathlib import Path

# Get the absolute path to the project root (parent of playground directory)
PROJECT_ROOT = Path(__file__).parent.parent.parent.absolute()

# Add project root and app directory to Python path
sys.path.insert(0, str(PROJECT_ROOT))

# Print debug information
print("Current working directory:", os.getcwd())
print("Project root:", PROJECT_ROOT)
print("Python path:", sys.path)

import logging
import nest_asyncio
from app.workflows.market_data_explorer_workflow import MarketDataExplorerWorkflow
from app.schemas.market_data_explorer_schema import MarketDataExplorerEvent

nest_asyncio.apply()

logging.basicConfig(level=logging.INFO)

# Create test event data
event_data = {
    "query": "you are yellow",
    "user_id": "user123",
    "session_id": "session456",
}

# Run workflow
workflow = MarketDataExplorerWorkflow()
result = workflow.run(event_data)
print(result)
