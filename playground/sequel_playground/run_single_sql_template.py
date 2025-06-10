"""
SQL Template Runner for Provider Analysis

This script allows you to easily run predefined SQL templates from sql_templates.py
by setting parameters at the top and executing the chosen template.

Available Templates:
- provider_specialty_distribution: Distribution of providers across specialties
- top_providers_by_specialty: Top providers by visit volume within specialties
- top_organizations_by_specialty: Leading organizations within specialties

Usage:
1. Set your desired parameters in the PARAMETERS section below
2. Choose which template to run by setting TEMPLATE_ID
3. Run the script in Jupyter or Python
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

    print("✅ Successfully imported SQL templates")
except ImportError as e:
    print(f"❌ Error importing SQL templates: {e}")
    exit()

# Database connection setup
try:
    DATABASE_URL = "postgresql://supabase_admin:your-super-secret-and-long-postgres-password@localhost:5433/postgres"  # Supabase local setup
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    print("✅ Successfully set up database connection")
except Exception as e:
    print(f"❌ Error setting up database connection: {e}")
    exit()

# =============================================================================
# CONFIGURATION SECTION - MODIFY THESE VALUES
# =============================================================================

# Choose which template to run
TEMPLATE_ID = "top_providers_by_specialty"

# Set your parameters here - adjust based on which template you're running
PARAMETERS = {
    # For provider_specialty_distribution
    "limit": 30,
    # For top_providers_by_specialty and top_organizations_by_specialty
    "specialty": "%Cardiology%",  # Set to %specialty% pattern if needed
    "top_n": 10,  # Show top 5 results per specialty
}

# =============================================================================
# EXECUTION SECTION - NO NEED TO MODIFY BELOW THIS LINE
# =============================================================================


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        return db
    except Exception as e:
        db.close()
        raise e


def run_template():
    """Execute the selected SQL template with the provided parameters."""

    # Check if template exists
    if TEMPLATE_ID not in SQL_TEMPLATES:
        print(f"❌ Template '{TEMPLATE_ID}' not found!")
        print(f"Available templates: {list(SQL_TEMPLATES.keys())}")
        return None

    template = SQL_TEMPLATES[TEMPLATE_ID]
    print(f"🔍 Running Template: {template.name}")
    print(f"📋 Description: {template.description}")
    print(f"⚙️ Template ID: {TEMPLATE_ID}")

    # Validate required parameters
    missing_params = []
    for param in template.required_params:
        if param not in PARAMETERS or PARAMETERS[param] is None:
            missing_params.append(param)

    if missing_params:
        print(f"❌ Missing required parameters: {missing_params}")
        print(f"Required parameters for this template: {template.required_params}")
        return None

    # Filter parameters to only include those needed for this template
    all_template_params = template.required_params + template.optional_params
    filtered_params = {k: v for k, v in PARAMETERS.items() if k in all_template_params}

    print(f"📊 Using parameters: {filtered_params}")

    # Get database session and execute query
    try:
        session = get_db()
        print("✅ Database connection established")

        # Execute the template
        query = text(template.sql)
        df = pd.read_sql(query, session.connection(), params=filtered_params)

        print(f"\n📊 Query Results: {len(df)} rows returned")
        print("-" * 80)

        if not df.empty:
            # Show column info
            print(f"Columns: {list(df.columns)}")
            print("-" * 80)

            # Display results
            pd.set_option("display.max_columns", None)
            pd.set_option("display.width", None)
            pd.set_option("display.max_colwidth", 50)
            print(df.to_string(index=False))
        else:
            print("⚠️ No results returned from the query")

        return df

    except Exception as e:
        print(f"❌ Error executing template: {e}")
        return None
    finally:
        if "session" in locals():
            session.close()
            print(f"\n🔌 Database connection closed")


def list_available_templates():
    """Display information about all available templates."""
    print("📋 AVAILABLE SQL TEMPLATES")
    print("=" * 80)

    for template_id, template in SQL_TEMPLATES.items():
        print(f"\n🔍 {template.name}")
        print(f"   ID: {template_id}")
        print(f"   Description: {template.description}")
        print(f"   Required Parameters: {', '.join(template.required_params)}")
        if template.optional_params:
            print(f"   Optional Parameters: {', '.join(template.optional_params)}")


def show_template_details(template_id: str):
    """Show detailed information about a specific template."""
    if template_id not in SQL_TEMPLATES:
        print(f"❌ Template '{template_id}' not found!")
        return

    template = SQL_TEMPLATES[template_id]
    print(f"📋 TEMPLATE DETAILS: {template.name}")
    print("=" * 80)
    print(f"ID: {template_id}")
    print(f"Description: {template.description}")
    print(f"Required Parameters: {template.required_params}")
    print(f"Optional Parameters: {template.optional_params}")
    print(f"Output Columns: {template.output_columns}")
    print(f"Keywords: {template.intent_keywords}")
    print(f"\nSQL Query:")
    print("-" * 40)
    print(template.sql)


if __name__ == "__main__":
    print("🚀 SQL TEMPLATE RUNNER")
    print("=" * 80)

    # Show what we're about to run
    print(f"Selected Template: {TEMPLATE_ID}")
    print(f"Parameters: {PARAMETERS}")
    print("-" * 80)

    # Run the template
    result_df = run_template()

    print("\n" + "=" * 80)
    print("💡 USAGE TIPS:")
    print("- Modify TEMPLATE_ID and PARAMETERS at the top of this script")
    print("- Use list_available_templates() to see all available templates")
    print("- Use show_template_details('template_id') for detailed template info")
