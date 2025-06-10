"""
Specialty Market Analysis Runner

This script runs multiple SQL templates to provide a comprehensive analysis of a single
specialty in the market. It combines provider, organization, and location data to give
a complete picture of the specialty's presence and performance.

Analysis includes:
- Top providers in the specialty
- Leading organizations
- Key practice locations
- Provider groups by location
- Top providers at each location
"""

import sys
import os
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the root directory to the Python path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# Import SQL templates
try:
    from playground.sequel_playground.sql_templates import SQL_TEMPLATES
    from app.services.sql_result_formatter import format_sql_result_for_llm

    print("✅ Successfully imported SQL templates and formatter")
except ImportError as e:
    print(f"❌ Error importing SQL templates: {e}")
    exit()

# Database connection setup
try:
    DATABASE_URL = "postgresql://supabase_admin:your-super-secret-and-long-postgres-password@localhost:5433/postgres"
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    print("✅ Successfully set up database connection")
except Exception as e:
    print(f"❌ Error setting up database connection: {e}")
    exit()

# =============================================================================
# CONFIGURATION SECTION - MODIFY THESE VALUES
# =============================================================================

# Specialty to analyze
SPECIALTY = (
    "%Cardiology%"  # Use SQL LIKE pattern (e.g., %Cardiology%, %Neurology%, etc.)
)

# Common filters that apply to all templates
COMMON_FILTERS = {
    "specialty": SPECIALTY,
    "state": None,  # Optional state filter (e.g., 'CA')
    "city": None,  # Optional city filter (e.g., '%San Francisco%')
}

# Template-specific parameters
TEMPLATE_PARAMETERS = {
    "top_providers_by_specialty": {
        "top_n": 20,  # Show more providers to get a comprehensive view
    },
    "top_organizations_by_specialty": {
        "top_n": 10,  # Show more organizations to understand market structure
    },
    "top_practice_locations": {
        "top_n": 10,  # Show more locations as they're key to geographic analysis
    },
    "practice_location_groups": {
        "top_n": 10,  # Show top groups per location
    },
    "top_providers_by_location": {
        "top_n": 5,  # Show top performers at each location
    },
}

# =============================================================================
# ANALYSIS FUNCTIONS
# =============================================================================


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        return db
    except Exception as e:
        db.close()
        raise e


def get_template_parameters(template_id: str) -> dict:
    """Get combined parameters for a specific template."""
    # Start with common filters
    params = COMMON_FILTERS.copy()

    # Add template-specific parameters if they exist
    if template_id in TEMPLATE_PARAMETERS:
        params.update(TEMPLATE_PARAMETERS[template_id])

    return params


def run_analysis_template(template_id: str) -> pd.DataFrame:
    """Run a single analysis template and return results."""
    if template_id not in SQL_TEMPLATES:
        print(f"❌ Template '{template_id}' not found!")
        return None

    template = SQL_TEMPLATES[template_id]
    print(f"\n🔍 Running Analysis: {template.name}")
    print(f"📋 {template.description}")

    # Get template-specific parameters
    params = get_template_parameters(template_id)
    print(f"⚙️ Using parameters: {params}")

    try:
        session = get_db()
        query = text(template.sql)
        df = pd.read_sql(query, session.connection(), params=params)

        if not df.empty:
            print(f"📊 Results: {len(df)} rows")
        else:
            print("⚠️ No results found")

        return df
    except Exception as e:
        print(f"❌ Error running analysis: {e}")
        return None
    finally:
        session.close()


def run_specialty_analysis():
    """Run comprehensive specialty analysis using multiple templates."""
    print(f"\n🏥 SPECIALTY MARKET ANALYSIS: {SPECIALTY}")
    print("=" * 80)

    analysis_results = {}

    # 1. Top Providers Analysis
    print("\n📊 PROVIDER ANALYSIS")
    print("-" * 40)
    analysis_results["top_providers"] = run_analysis_template(
        "top_providers_by_specialty"
    )

    # 2. Organization Analysis
    print("\n🏢 ORGANIZATION ANALYSIS")
    print("-" * 40)
    analysis_results["top_organizations"] = run_analysis_template(
        "top_organizations_by_specialty"
    )

    # 3. Practice Locations Analysis
    print("\n📍 PRACTICE LOCATIONS ANALYSIS")
    print("-" * 40)
    analysis_results["top_locations"] = run_analysis_template("top_practice_locations")

    # 4. Provider Groups by Location
    print("\n👥 PROVIDER GROUPS BY LOCATION")
    print("-" * 40)
    analysis_results["location_groups"] = run_analysis_template(
        "practice_location_groups"
    )

    # 5. Top Providers by Location
    print("\n🌟 TOP PROVIDERS BY LOCATION")
    print("-" * 40)
    analysis_results["providers_by_location"] = run_analysis_template(
        "top_providers_by_location"
    )

    return analysis_results


def display_analysis_summary(results: dict):
    """Display a summary of the analysis results."""
    print("\n📈 ANALYSIS SUMMARY")
    print("=" * 80)

    if not results:
        print("❌ No analysis results available")
        return

    # Provider Summary
    if "top_providers" in results and not results["top_providers"].empty:
        df = results["top_providers"]
        print("\n🏆 TOP PROVIDERS")
        print("-" * 40)
        print(df.to_string(index=False))

    # Organization Summary
    if "top_organizations" in results and not results["top_organizations"].empty:
        df = results["top_organizations"]
        print("\n🏢 TOP ORGANIZATIONS")
        print("-" * 40)
        print(df.to_string(index=False))

    # Location Summary
    if "top_locations" in results and not results["top_locations"].empty:
        df = results["top_locations"]
        print("\n📍 TOP LOCATIONS")
        print("-" * 40)
        print(df.to_string(index=False))

    # Provider Groups Summary
    if "location_groups" in results and not results["location_groups"].empty:
        df = results["location_groups"]
        print("\n👥 PROVIDER GROUPS")
        print("-" * 40)
        print(df.to_string(index=False))

    # Providers by Location Summary
    if (
        "providers_by_location" in results
        and not results["providers_by_location"].empty
    ):
        df = results["providers_by_location"]
        print("\n🌟 PROVIDERS BY LOCATION")
        print("-" * 40)
        print(df.to_string(index=False))


def format_results_for_llm(results: dict) -> dict:
    """
    Takes the analysis results and formats them for LLM consumption.
    This function can be called separately after running the main analysis.

    Args:
        results: Dictionary containing the analysis results from run_specialty_analysis()

    Returns:
        Dictionary containing LLM-formatted strings for each analysis type
    """
    llm_formatted = {}

    # Format top providers results
    if "top_providers" in results and not results["top_providers"].empty:
        llm_formatted["top_providers"] = format_sql_result_for_llm(
            df=results["top_providers"],
            template_id="top_providers_by_specialty",
            template_info=SQL_TEMPLATES["top_providers_by_specialty"].__dict__,
        )

    # Format top organizations results
    if "top_organizations" in results and not results["top_organizations"].empty:
        llm_formatted["top_organizations"] = format_sql_result_for_llm(
            df=results["top_organizations"],
            template_id="top_organizations_by_specialty",
            template_info=SQL_TEMPLATES["top_organizations_by_specialty"].__dict__,
        )

    return llm_formatted


def display_llm_formatted_results(formatted_results: dict):
    """
    Display the LLM-formatted results in a readable way.

    Args:
        formatted_results: Dictionary containing LLM-formatted strings
    """
    print("\n🤖 LLM-FORMATTED ANALYSIS")
    print("=" * 80)

    for analysis_type, formatted_text in formatted_results.items():
        print(f"\n📊 {analysis_type.upper()}:")
        print("-" * 40)
        print(formatted_text)
        print("\n")


display_llm_formatted_results(format_results_for_llm(results))

if __name__ == "__main__":
    # Configure pandas display settings
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", None)
    pd.set_option("display.max_colwidth", 50)

    # Run the analysis
    results = run_specialty_analysis()

    # Display regular results
    display_analysis_summary(results)

    # Optional: Format and display results for LLM consumption
    print("\nWould you like to see the LLM-formatted version? (y/n)")
    if input().lower() == "y":
        llm_formatted = format_results_for_llm(results)
        display_llm_formatted_results(llm_formatted)

    print("\n" + "=" * 80)
    print("💡 USAGE TIPS:")
    print(
        "- Modify SPECIALTY at the top of this script to analyze different specialties"
    )
    print("- Adjust COMMON_FILTERS to apply filters across all templates")
    print("- Modify TEMPLATE_PARAMETERS to customize results for each analysis type")
    print("- Results are returned as pandas DataFrames for further analysis")
