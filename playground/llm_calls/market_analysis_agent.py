"""
Market Analysis LLM Agent

This script uses PydanticAI to create an agent that can analyze healthcare market data
and provide structured insights.
"""

from typing import Dict, List, Optional
import nest_asyncio
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.exceptions import ModelRetry
import os
from dotenv import load_dotenv
from pathlib import Path

# Try to load environment variables from multiple possible locations
env_locations = [
    ".env",  # Current directory
    "../.env",  # Parent directory
    "../../.env",  # Root directory
    "../../app/.env",  # App directory
]

env_loaded = False
for env_path in env_locations:
    if Path(env_path).exists():
        load_dotenv(env_path)
        print(f"✅ Loaded environment variables from {env_path}")
        env_loaded = True
        break

if not env_loaded:
    print("❌ No .env file found. Please create one with your OPENAI_API_KEY")
    print("Possible locations to place your .env file:")
    for loc in env_locations:
        print(f"- {Path(loc).absolute()}")
    exit(1)

# Verify OpenAI API key is available
if not os.getenv("OPENAI_API_KEY"):
    print("❌ OPENAI_API_KEY not found in environment variables")
    print("Please add OPENAI_API_KEY=your-key-here to your .env file")
    exit(1)

# Apply nest_asyncio for interactive python environments
nest_asyncio.apply()


class MarketInsight(BaseModel):
    """Structured insights about the healthcare market analysis."""

    key_findings: List[str] = Field(
        description="List of main insights from the market analysis"
    )
    market_leaders: List[str] = Field(
        description="Key organizations or providers leading the market"
    )
    market_trends: str = Field(description="Overall trends observed in the market data")
    recommendations: List[str] = Field(
        description="Strategic recommendations based on the analysis"
    )
    confidence_score: float = Field(
        description="Confidence in the analysis (0-1)", ge=0, le=1
    )


# Create the market analysis agent
market_agent = Agent(
    model="openai:gpt-4",
    output_type=MarketInsight,
    instructions="""
    You are an expert healthcare market analyst. Your role is to:
    1. Analyze healthcare market data thoroughly
    2. Identify key market leaders and trends
    3. Provide actionable insights and recommendations
    4. Focus on data-driven observations
    5. Be precise and quantitative where possible
    
    Format your analysis in a structured way that highlights:
    - Key findings from the data
    - Market leaders and their strengths
    - Notable market trends
    - Strategic recommendations
    """,
)


def analyze_market_data(formatted_data: str) -> MarketInsight:
    """
    Analyze market data using the LLM agent.

    Args:
        formatted_data: String containing the formatted market analysis data

    Returns:
        MarketInsight object containing structured analysis
    """
    prompt = f"""
    Please analyze the following healthcare market data and provide structured insights:
    
    {formatted_data}
    
    Focus on:
    1. Key market dynamics and patterns
    2. Leading organizations and providers
    3. Market concentration and competition
    4. Geographic distribution if applicable
    5. Opportunities and potential risks
    """

    response = market_agent.run_sync(
        user_prompt=prompt,
        model_settings={
            "temperature": 0.3  # Lower temperature for more focused analysis
        },
    )

    return response.output


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
    insights = analyze_market_data(example_data)

    # Print results
    print("\n🔍 MARKET ANALYSIS INSIGHTS")
    print("=" * 50)

    print("\n📊 Key Findings:")
    for finding in insights.key_findings:
        print(f"- {finding}")

    print("\n🏆 Market Leaders:")
    for leader in insights.market_leaders:
        print(f"- {leader}")

    print("\n📈 Market Trends:")
    print(insights.market_trends)

    print("\n💡 Recommendations:")
    for rec in insights.recommendations:
        print(f"- {rec}")

    print(f"\n✨ Confidence Score: {insights.confidence_score:.2f}")
