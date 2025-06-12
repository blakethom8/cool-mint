"""
Procedure Code Analysis Runner

This script allows you to run predefined SQL templates for analyzing procedure codes
from proc_code_sql_template.py by setting parameters and executing the chosen template.

Available Templates:
- surgical_cardio_procedures: Shows surgical procedures related to cardiology
- procedure_type_distribution: Shows distribution of procedures across types

Usage:
1. Set your desired parameters in the PARAMETERS section below
2. Choose which template to run by setting TEMPLATE_ID
3. Run the script
"""

import sys
import os
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the root directory to the Python path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# Import SQL templates
try:
    from playground.sequel_playground.sql_proc_code.proc_code_sql_template import (
        PROC_CODE_TEMPLATES,
    )

    # Import the SQL result formatter for LLM processing
    from app.services.sql_result_formatter import format_sql_result_for_llm

    print("✅ Successfully imported procedure code SQL templates and formatter")
except ImportError as e:
    print(f"❌ Error importing SQL templates or formatter: {e}")
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

# Choose which template to run
TEMPLATE_ID = "surgical_cardio_procedures"

# Set your parameters here - adjust based on which template you're running
PARAMETERS = {
    "limit": 20  # Show top 20 surgical cardio procedures
}

# =============================================================================
# EXECUTION SECTION
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
    if TEMPLATE_ID not in PROC_CODE_TEMPLATES:
        print(f"❌ Template '{TEMPLATE_ID}' not found!")
        print(f"Available templates: {list(PROC_CODE_TEMPLATES.keys())}")
        return None

    template = PROC_CODE_TEMPLATES[TEMPLATE_ID]
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


def format_results_for_llm(df: pd.DataFrame, template_id: str) -> str:
    """
    Format the SQL results for LLM consumption.

    Args:
        df: DataFrame containing the query results
        template_id: The template ID used to generate the results

    Returns:
        Formatted string ready for LLM processing
    """
    if df is None or df.empty:
        return "No data available for formatting."

    template_info = PROC_CODE_TEMPLATES[template_id].__dict__

    try:
        formatted_text = format_sql_result_for_llm(
            df=df, template_id=template_id, template_info=template_info
        )
        return formatted_text
    except Exception as e:
        print(f"❌ Error formatting results for LLM: {e}")
        return f"Error formatting results: {str(e)}"


def list_available_templates():
    """Display information about all available templates."""
    print("📋 AVAILABLE PROCEDURE CODE TEMPLATES")
    print("=" * 80)

    for template_id, template in PROC_CODE_TEMPLATES.items():
        print(f"\n🔍 {template.name}")
        print(f"   ID: {template_id}")
        print(f"   Description: {template.description}")
        print(f"   Required Parameters: {', '.join(template.required_params)}")
        if template.optional_params:
            print(f"   Optional Parameters: {', '.join(template.optional_params)}")


def show_template_details(template_id: str):
    """Show detailed information about a specific template."""
    if template_id not in PROC_CODE_TEMPLATES:
        print(f"❌ Template '{template_id}' not found!")
        return

    template = PROC_CODE_TEMPLATES[template_id]
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
    print("🚀 PROCEDURE CODE ANALYSIS RUNNER")
    print("=" * 80)

    # Show what we're about to run
    print(f"Selected Template: {TEMPLATE_ID}")
    print(f"Parameters: {PARAMETERS}")
    print("-" * 80)

    # Run the template
    result_df = run_template()

    # Format results for LLM if requested
    if result_df is not None and not result_df.empty:
        print("\n" + "=" * 80)
        print("🤖 LLM-FORMATTED RESULTS")
        print("=" * 80)

        formatted_results = format_results_for_llm(result_df, TEMPLATE_ID)
        print(formatted_results)

        # Save formatted results to a variable for easy copying
        print("\n💾 Formatted results saved to 'formatted_results' variable")
        print(
            "You can copy this output and use it with the procedure categorization agent."
        )

    print("\n" + "=" * 80)
    print("💡 USAGE TIPS:")
    print("- Modify TEMPLATE_ID and PARAMETERS at the top of this script")
    print("- Use list_available_templates() to see all available templates")
    print("- Use show_template_details('template_id') for detailed template info")
    print("- The LLM-formatted results can be used with proc_detail_cat_agent.py")
    print(
        "- Copy the formatted output above and paste it into the categorization agent"
    )
