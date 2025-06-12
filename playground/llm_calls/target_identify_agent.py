"""
Target Identification Agent

This script uses PydanticAI to analyze healthcare provider data and identify
high-potential targets for referral network development.
"""

from typing import Dict, List, Optional
import nest_asyncio
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.exceptions import ModelRetry
import os
from dotenv import load_dotenv
from pathlib import Path


def find_project_root(current_path: str) -> str:
    """Find the project root directory by looking for specific markers."""
    path = Path(current_path).resolve()

    # Keep going up until we find the project root or hit the filesystem root
    while path != path.parent:
        # Check for common project root markers
        if (path / "app").exists() or (path / ".git").exists():
            return str(path)
        path = path.parent

    # If we didn't find a marker, return the original directory
    return current_path


# Get the absolute path to the script's directory and project root
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = find_project_root(current_dir)

print(f"Current directory: {current_dir}")
print(f"Project root: {project_root}")

# Try to load environment variables from multiple possible locations
env_locations = [
    os.path.join(project_root, "app", ".env"),  # App directory
    os.path.join(project_root, ".env"),  # Root directory
    os.path.join(current_dir, ".env"),  # Current directory
    os.path.join(os.path.dirname(current_dir), ".env"),  # Parent directory
]

env_loaded = False
for env_path in env_locations:
    print(f"Checking for .env file at: {env_path}")
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"✅ Loaded environment variables from {env_path}")
        env_loaded = True
        break

if not env_loaded:
    print("\n❌ No .env file found. Please create one with your OPENAI_API_KEY")
    print("Possible locations to place your .env file:")
    for loc in env_locations:
        print(f"- {loc}")
    print("\nRecommended location: {}/app/.env".format(project_root))
    exit(1)

# Verify OpenAI API key is available
if not os.getenv("OPENAI_API_KEY"):
    print("❌ OPENAI_API_KEY not found in environment variables")
    print("Please add OPENAI_API_KEY=your-key-here to your .env file")
    exit(1)

# Apply nest_asyncio for interactive python environments
nest_asyncio.apply()


class TargetProvider(BaseModel):
    """Individual provider target information."""

    name: str = Field(description="Provider's full name")
    organization: str = Field(description="Provider's primary organization")
    practice_location: str = Field(description="Provider's practice location")
    visit_volume: int = Field(description="Provider's total visit volume")
    rationale: List[str] = Field(
        description="Specific reasons why this provider would be a good referral target",
        default_factory=list,
    )
    opportunity_score: float = Field(
        description="Score indicating the strength of the referral opportunity (0-1)",
        ge=0,
        le=1,
        default=0.5,
    )


class ReferralTargets(BaseModel):
    """Structured output for referral target identification."""

    priority_targets: List[TargetProvider] = Field(
        description="High-priority providers to target for referral network development",
        max_items=5,
        default_factory=list,
    )

    market_insights: List[str] = Field(
        description="Key insights about the market and referral opportunities",
        default_factory=list,
    )

    network_gaps: List[str] = Field(
        description="Identified gaps in current referral network coverage",
        default_factory=list,
    )

    approach_recommendations: Dict[str, List[str]] = Field(
        description="Recommended approach strategies for each target provider",
        default_factory=dict,
    )

    overall_confidence: float = Field(
        description="Overall confidence in the target recommendations (0-1)",
        ge=0,
        le=1,
        default=0.5,
    )

    class Config:
        validate_assignment = True


# Create the target identification agent
target_agent = Agent(
    model="openai:gpt-4",
    output_type=ReferralTargets,
    instructions="""
    You are an expert healthcare referral network analyst. Your role is to identify and analyze potential referral targets.
    
    IMPORTANT: You must provide ALL of the following in your response:
    1. priority_targets: List of TargetProvider objects (up to 5 providers)
    2. market_insights: List of string insights
    3. network_gaps: List of string gaps
    4. approach_recommendations: Dictionary mapping provider names to lists of approach strategies
    5. overall_confidence: Float between 0 and 1
    
    For each TargetProvider, you must include:
    - name: Provider's full name
    - organization: Primary organization
    - practice_location: Practice location
    - visit_volume: Total visit volume (integer)
    - rationale: List of reasons for selection
    - opportunity_score: Float between 0 and 1
    
    Example format:
    {
        "priority_targets": [
            {
                "name": "John Smith",
                "organization": "UCSF Health",
                "practice_location": "San Francisco",
                "visit_volume": 3000,
                "rationale": ["High volume", "Strategic location"],
                "opportunity_score": 0.85
            }
        ],
        "market_insights": ["Insight 1", "Insight 2"],
        "network_gaps": ["Gap 1", "Gap 2"],
        "approach_recommendations": {
            "Dr. John Smith": ["Strategy 1", "Strategy 2"]
        },
        "overall_confidence": 0.8
    }
    
    When analyzing, consider:
    - Visit volume and patient flow
    - Geographic coverage and accessibility
    - Organizational relationships
    - Practice focus and specialization
    - Potential for mutual benefit
    """,
)


def identify_referral_targets(market_data: str) -> ReferralTargets:
    """
    Analyze market data to identify potential referral network targets.

    Args:
        market_data: String containing the formatted market analysis data

    Returns:
        ReferralTargets object containing target recommendations and insights
    """
    prompt = f"""
    Please analyze this healthcare market data to identify the best targets 
    for referral network development. Ensure your response includes ALL required fields
    in the exact format specified:
    
    {market_data}
    
    Required Analysis Points:
    1. Identify up to 5 high-priority target providers
    2. Provide market insights
    3. Identify network gaps
    4. Create specific approach recommendations for EACH target provider
    5. Assess overall confidence in recommendations
    
    Remember to include approach_recommendations as a dictionary mapping provider names
    to their specific approach strategies.
    """

    try:
        response = target_agent.run_sync(
            user_prompt=prompt,
            model_settings={
                "temperature": 0.4,  # Balanced between creativity and precision
                "response_format": {"type": "json_object"},  # Enforce JSON formatting
            },
        )
        return response.output
    except Exception as e:
        print(f"Error in target identification: {str(e)}")
        # Return a minimal valid object if there's an error
        return ReferralTargets(
            priority_targets=[],
            market_insights=["Error in analysis"],
            network_gaps=["Unable to identify gaps"],
            approach_recommendations={},
            overall_confidence=0.0,
        )


# Example usage:
if __name__ == "__main__":
    # Example formatted data (you would replace this with your actual formatted data)
    example_data = """
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
  * Organization: Northern California Cardiovascular Group
  * Practice: Bay Area Cardiology Associates
  * Total Visits: 2,874



TOP_ORGANIZATIONS:
----------------------------------------
Analysis Type: Top Organizations by Specialty
Analysis Time: 2025-06-09 21:48:25
Total Organizations Analyzed: 10

Key Statistics:
- Total Provider Count: 158
- Average Providers per Organization: 15.8

Detailed Organization Analysis:

Specialty: Cardiology
Number of Organizations: 10
Market Leaders:
- Independent Practice
  * Provider Count: 33
  * Market Position: Rank 1
- UCSF Health
  * Provider Count: 18
  * Market Position: Rank 2
- Bay Area Surgical Specialists
  * Provider Count: 16
  * Market Position: Rank 3
- Peninsula Orthopedic Associates
  * Provider Count: 15
  * Market Position: Rank 4
- Bay Area Cancer Care
  * Provider Count: 14
  * Market Position: Rank 5
- El Camino Health
  * Provider Count: 14
  * Market Position: Rank 6
- CommonSpirit Health
  * Provider Count: 13
  * Market Position: Rank 7
- Northern California Cardiovascular Group
  * Provider Count: 12
  * Market Position: Rank 8
- Santa Clara Valley Medical Center
  * Provider Count: 12
  * Market Position: Rank 9
- John Muir Health
  * Provider Count: 11
  * Market Position: Rank 10

    """

    # Run the analysis
    targets = identify_referral_targets(example_data)

    # Print results
    print("\n🎯 REFERRAL TARGET RECOMMENDATIONS")
    print("=" * 50)

    print("\n🏆 Priority Targets:")
    for target in targets.priority_targets:
        print(f"\nDr. {target.name}")
        print(f"Organization: {target.organization}")
        print(f"Location: {target.practice_location}")
        print(f"Visit Volume: {target.visit_volume:,}")
        print("Rationale:")
        for reason in target.rationale:
            print(f"  - {reason}")
        print(f"Opportunity Score: {target.opportunity_score:.2f}")

    print("\n📊 Market Insights:")
    for insight in targets.market_insights:
        print(f"- {insight}")

    print("\n🔍 Network Gaps:")
    for gap in targets.network_gaps:
        print(f"- {gap}")

    print("\n💡 Approach Recommendations:")
    for provider, approaches in targets.approach_recommendations.items():
        print(f"\nFor {provider}:")
        for approach in approaches:
            print(f"- {approach}")

    print(f"\n✨ Overall Confidence Score: {targets.overall_confidence:.2f}")
