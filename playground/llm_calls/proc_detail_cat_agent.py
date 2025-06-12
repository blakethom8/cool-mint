"""
Procedure Code Categorization Agent

This script uses PydanticAI to analyze procedure codes and categorize them
by complexity level (High, Medium, Low) based on their descriptions and metadata.
"""

from typing import Dict, List, Optional, Literal
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


class CategorizedProcedure(BaseModel):
    """Individual procedure with categorization."""

    procedure_code: str = Field(description="The CPT or procedure code")
    procedure_description: str = Field(description="Full description of the procedure")
    complexity_category: Literal["High", "Medium", "Low"] = Field(
        description="Complexity level categorization"
    )
    rationale: List[str] = Field(
        description="Specific reasons for the complexity categorization",
        default_factory=list,
    )
    confidence_score: float = Field(
        description="Confidence in the categorization (0-1)",
        ge=0,
        le=1,
        default=0.5,
    )
    visit_volume: int = Field(
        description="Number of visits for this procedure", default=0
    )


class ProcedureCategorizationResults(BaseModel):
    """Structured output for procedure code categorization."""

    categorized_procedures: List[CategorizedProcedure] = Field(
        description="List of procedures with their complexity categorizations",
        default_factory=list,
    )

    category_distribution: Dict[str, int] = Field(
        description="Count of procedures in each complexity category",
        default_factory=dict,
    )

    analysis_insights: List[str] = Field(
        description="Key insights from the categorization analysis",
        default_factory=list,
    )

    categorization_criteria: Dict[str, List[str]] = Field(
        description="Criteria used for each complexity level",
        default_factory=dict,
    )

    overall_confidence: float = Field(
        description="Overall confidence in the categorizations (0-1)",
        ge=0,
        le=1,
        default=0.5,
    )

    class Config:
        validate_assignment = True


# Create the procedure categorization agent
categorization_agent = Agent(
    model="openai:gpt-4",
    output_type=ProcedureCategorizationResults,
    instructions="""
    You are an expert medical procedure analyst specializing in categorizing healthcare procedures by complexity.
    
    IMPORTANT: You must provide ALL of the following in your response:
    1. categorized_procedures: List of CategorizedProcedure objects
    2. category_distribution: Dictionary with counts for each complexity level
    3. analysis_insights: List of key insights from the analysis
    4. categorization_criteria: Dictionary explaining criteria for each complexity level
    5. overall_confidence: Float between 0 and 1
    
    For each CategorizedProcedure, you must include:
    - procedure_code: The CPT or procedure code
    - procedure_description: Full description
    - complexity_category: "High", "Medium", or "Low"
    - rationale: List of specific reasons for the categorization
    - confidence_score: Float between 0 and 1
    - visit_volume: Integer number of visits
    
    COMPLEXITY CATEGORIZATION GUIDELINES:
    
    HIGH COMPLEXITY:
    - Major surgical procedures requiring specialized skills
    - Procedures with high risk of complications
    - Multi-step or multi-organ procedures
    - Procedures requiring advanced technology/equipment
    - Long procedure duration (typically >2 hours)
    - Examples: Open heart surgery, complex valve repairs, CABG
    
    MEDIUM COMPLEXITY:
    - Moderately invasive procedures
    - Procedures requiring specialized training but lower risk
    - Standard surgical techniques with moderate complexity
    - Procedures with moderate recovery time
    - Examples: Catheter ablations, pacemaker insertions, angioplasty
    
    LOW COMPLEXITY:
    - Minimally invasive or diagnostic procedures
    - Routine procedures with low risk
    - Short duration procedures
    - Procedures that can be done on outpatient basis
    - Examples: ECGs, stress tests, echocardiograms, basic diagnostics
    
    Consider these factors when categorizing:
    - Invasiveness of the procedure
    - Risk level and potential complications
    - Required expertise and training
    - Duration and recovery time
    - Equipment and facility requirements
    """,
)


def categorize_procedures(procedure_data: str) -> ProcedureCategorizationResults:
    """
    Analyze procedure code data and categorize by complexity.

    Args:
        procedure_data: String containing the formatted procedure code data

    Returns:
        ProcedureCategorizationResults object containing categorizations and analysis
    """
    prompt = f"""
    Please analyze the following procedure code data and categorize each procedure
    by complexity level (High, Medium, Low). Ensure your response includes ALL required fields:
    
    {procedure_data}
    
    Required Analysis:
    1. Categorize each procedure by complexity level with clear rationale
    2. Provide category distribution counts
    3. Generate key insights from the analysis
    4. Explain the criteria used for each complexity level
    5. Assess overall confidence in categorizations
    
    Remember to include specific rationale for each procedure's categorization
    based on medical complexity, invasiveness, risk level, and required expertise.
    """

    try:
        response = categorization_agent.run_sync(
            user_prompt=prompt,
            model_settings={
                "temperature": 0.3,  # Lower temperature for more consistent categorization
                "response_format": {"type": "json_object"},  # Enforce JSON formatting
            },
        )
        return response.output
    except Exception as e:
        print(f"Error in procedure categorization: {str(e)}")
        # Return a minimal valid object if there's an error
        return ProcedureCategorizationResults(
            categorized_procedures=[],
            category_distribution={},
            analysis_insights=["Error in categorization analysis"],
            categorization_criteria={},
            overall_confidence=0.0,
        )


# Example usage and testing function
if __name__ == "__main__":
    # Example formatted procedure data (you would replace this with actual formatted data)
    example_data = """
Analysis Type: Surgical Cardio Procedures
Analysis Time: 2025-06-09 21:48:25
Total Procedures Analyzed: 5

Procedure Summary:
- Total Visit Volume: 15,000
- Average Visits per Procedure: 3,000
- Procedure Types: 1
- Procedure Sub Types: 1

Detailed Procedure Analysis:

Procedure 1:
- Code: 33533
- Description: Coronary artery bypass, using arterial graft(s); single arterial graft
- Type: Surgical
- Sub Type: Cardiothoracic Surgery
- Visit Volume: 3,500

Procedure 2:
- Code: 93458
- Description: Catheter placement in coronary artery(s) for coronary angiography
- Type: Surgical
- Sub Type: Cardiovascular Medicine
- Visit Volume: 3,200

Procedure 3:
- Code: 93306
- Description: Echocardiography, transthoracic, complete
- Type: Diagnostic
- Sub Type: Cardiovascular Medicine
- Visit Volume: 3,100

Procedure 4:
- Code: 33249
- Description: Insertion of permanent pacing cardioverter-defibrillator system
- Type: Surgical
- Sub Type: Cardiothoracic Surgery
- Visit Volume: 2,800

Procedure 5:
- Code: 93000
- Description: Electrocardiogram, routine ECG with at least 12 leads
- Type: Diagnostic
- Sub Type: Cardiovascular Medicine
- Visit Volume: 2,400
    """

    # Run the categorization
    results = categorize_procedures(example_data)

    # Display results
    print("\n🏥 PROCEDURE COMPLEXITY CATEGORIZATION RESULTS")
    print("=" * 60)

    print("\n📊 Categorized Procedures:")
    for proc in results.categorized_procedures:
        print(f"\n🔍 {proc.procedure_code} - {proc.complexity_category} Complexity")
        print(f"Description: {proc.procedure_description}")
        print(f"Visit Volume: {proc.visit_volume:,}")
        print("Rationale:")
        for reason in proc.rationale:
            print(f"  - {reason}")
        print(f"Confidence: {proc.confidence_score:.2f}")

    print("\n📈 Category Distribution:")
    for category, count in results.category_distribution.items():
        print(f"- {category}: {count} procedures")

    print("\n💡 Analysis Insights:")
    for insight in results.analysis_insights:
        print(f"- {insight}")

    print("\n📋 Categorization Criteria:")
    for category, criteria in results.categorization_criteria.items():
        print(f"\n{category} Complexity:")
        for criterion in criteria:
            print(f"  - {criterion}")

    print(f"\n✨ Overall Confidence Score: {results.overall_confidence:.2f}")
