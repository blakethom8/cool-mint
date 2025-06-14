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

# Example market data for testing
EXAMPLE_MARKET_DATA = """
TOP_PROVIDERS:
----------------------------------------
Analysis Type: Top Providers by Specialty
Analysis Time: 2025-06-09 21:48:25
Total Providers Analyzed: 20

Key Statistics:
- Total Visit Volume: 61,255
- Average Visits per Provider: 3,062.8
- Number of Organizations: 11
- Number of Practice Locations: 19

Detailed Provider Analysis:

Specialty: Cardiology
Number of Providers: 20
Top Providers:
- Dr. Elizabeth Long
  * Organization: UCSF Health
  * Practice: East Bay Cancer Center
  * Total Visits: 3,557
- Dr. Douglas Anderson
  * Organization: Kaiser Permanente Northern California
  * Practice: Washington Hospital Healthcare System
  * Total Visits: 3,284
- Dr. Cynthia Evans
  * Organization: UCSF Health
  * Practice: Marin Medical Collective
  * Total Visits: 3,251
- Dr. Joseph Phillips
  * Organization: John Muir Health
  * Practice: El Camino Health
  * Total Visits: 3,204
- Dr. Brandon Powell
  * Organization: Bay Area Cancer Care
  * Practice: UCSF Health Network
  * Total Visits: 3,163
- Dr. Angela Thompson
  * Organization: Independent Practice
  * Practice: Santa Clara Valley Medical Center
  * Total Visits: 3,157
- Dr. Jacob Anderson
  * Organization: Bay Area Surgical Specialists
  * Practice: East Bay Cardiovascular Group
  * Total Visits: 3,053
- Dr. Cynthia Simmons
  * Organization: John Muir Health
  * Practice: Pacific Specialty Partners
  * Total Visits: 3,041
- Dr. Joshua Ward
  * Organization: Sutter Health
  * Practice: Pacific Primary Care
  * Total Visits: 3,033
- Dr. Joseph Hall
  * Organization: El Camino Health
  * Practice: SF Skin & Laser Center
  * Total Visits: 3,031
- Dr. Patricia Martinez
  * Organization: Stanford Health Care
  * Practice: Golden Gate Orthopedics
  * Total Visits: 3,011
- Dr. Adam Ross
  * Organization: Independent Practice
  * Practice: Marin Orthopedic Group
  * Total Visits: 3,006
- Dr. Kevin Bell
  * Organization: Northern California Cardiovascular Group
  * Practice: SF Orthopedic Institute
  * Total Visits: 3,001
- Dr. Frances Peterson
  * Organization: Independent Practice
  * Practice: Bay Area Comprehensive Care
  * Total Visits: 3,000
- Dr. Cynthia Powell
  * Organization: Northern California Cardiovascular Group
  * Practice: Bay Area Bone & Joint
  * Total Visits: 2,961
- Dr. Jason Morgan
  * Organization: Bay Area Surgical Specialists
  * Practice: SF Skin & Laser Center
  * Total Visits: 2,927
- Dr. Linda Bailey
  * Organization: El Camino Health
  * Practice: SF NeuroCare Partners
  * Total Visits: 2,914
- Dr. Jonathan Alexander
  * Organization: Bay Area Cancer Care
  * Practice: John Muir Health
  * Total Visits: 2,911
- Dr. Larry Coleman
  * Organization: Peninsula Orthopedic Associates
  * Practice: Pacific Neurological Institute
  * Total Visits: 2,876
- Dr. Stephen Barnes
"""

# Test 1: Search Classification
print("\n=== Testing Search Classification ===")
search_event = {
    "query": "What are the top healthcare providers in the Bay Area?",
    "user_id": "user123",
    "session_id": "session456",
}

workflow = MarketDataExplorerWorkflow()
search_result = workflow.run(search_event)
print("\nSearch Classification Result:")
print(f"Needs Search: {search_result.data.get('needs_search')}")
print(f"Reason: {search_result.data.get('reason')}")

# Test 2: Target Identification
print("\n=== Testing Target Identification ===")
target_event = {
    "query": "Identify potential referral targets",
    "market_data": EXAMPLE_MARKET_DATA,
    "user_id": "user123",
    "session_id": "session456",
}

target_result = workflow.run(target_event)
print("\nTarget Identification Result:")
target_data = target_result.data.get("target_identification", {})
if target_data:
    print("\nPriority Targets:")
    for target in target_data.get("priority_targets", []):
        print(f"\n- {target.name}")
        print(f"  Organization: {target.organization}")
        print(f"  Location: {target.practice_location}")
        print(f"  Visit Volume: {target.visit_volume}")
        print(f"  Opportunity Score: {target.opportunity_score}")

    print("\nMarket Insights:")
    for insight in target_data.get("market_insights", []):
        print(f"- {insight}")

    print("\nNetwork Gaps:")
    for gap in target_data.get("network_gaps", []):
        print(f"- {gap}")

    print(f"\nOverall Confidence: {target_data.get('overall_confidence', 0)}")
else:
    print("No target identification data available")
