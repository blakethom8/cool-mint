"""
Complete Procedure Code Categorization Workflow

This script runs the complete workflow:
1. Execute SQL query for surgical cardio procedures
2. Format results for LLM consumption
3. Run categorization analysis using the LLM agent
4. Display categorized results

This combines explore_proc_db.py and proc_detail_cat_agent.py into one seamless workflow.
"""

import sys
import os
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Add the root directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
playground_root = os.path.dirname(os.path.dirname(current_dir))
root_dir = os.path.dirname(playground_root)

sys.path.insert(0, root_dir)
sys.path.insert(0, playground_root)

# Load environment variables
env_path = os.path.join(root_dir, "app", ".env")
load_dotenv(env_path)

# Import required modules
try:
    from playground.sequel_playground.sql_proc_code.proc_code_sql_template import (
        PROC_CODE_TEMPLATES,
    )
    from app.services.sql_result_formatter import format_sql_result_for_llm
    from playground.llm_calls.proc_detail_cat_agent import categorize_procedures

    print("✅ Successfully imported all required modules")
except ImportError as e:
    print(f"❌ Error importing modules: {e}")
    print(f"Python path: {sys.path}")
    exit()

# Database connection setup
try:
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        DATABASE_URL = "postgresql://supabase_admin:your-super-secret-and-long-postgres-password@localhost:5433/postgres"
        print("⚠️ Using default DATABASE_URL")

    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    print("✅ Successfully set up database connection")
except Exception as e:
    print(f"❌ Error setting up database connection: {e}")
    exit()

# =============================================================================
# CONFIGURATION SECTION
# =============================================================================

TEMPLATE_ID = "surgical_cardio_procedures"
PARAMETERS = {
    "limit": 10  # Number of procedures to analyze
}

# =============================================================================
# WORKFLOW FUNCTIONS
# =============================================================================


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        return db
    except Exception as e:
        db.close()
        raise e


def run_sql_query() -> pd.DataFrame:
    """Execute the SQL query and return results."""
    print(f"\n🔍 Step 1: Running SQL Query - {TEMPLATE_ID}")
    print("-" * 50)

    if TEMPLATE_ID not in PROC_CODE_TEMPLATES:
        print(f"❌ Template '{TEMPLATE_ID}' not found!")
        return None

    template = PROC_CODE_TEMPLATES[TEMPLATE_ID]
    print(f"📋 Template: {template.name}")
    print(f"📊 Parameters: {PARAMETERS}")

    try:
        session = get_db()
        query = text(template.sql)
        df = pd.read_sql(query, session.connection(), params=PARAMETERS)

        print(f"✅ Query executed successfully - {len(df)} procedures found")
        return df

    except Exception as e:
        print(f"❌ Error executing SQL query: {e}")
        return None
    finally:
        if "session" in locals():
            session.close()


def format_for_llm(df: pd.DataFrame) -> str:
    """Format SQL results for LLM consumption."""
    print(f"\n📝 Step 2: Formatting Results for LLM")
    print("-" * 50)

    if df is None or df.empty:
        print("❌ No data to format")
        return None

    template_info = PROC_CODE_TEMPLATES[TEMPLATE_ID].__dict__

    try:
        formatted_text = format_sql_result_for_llm(
            df=df, template_id=TEMPLATE_ID, template_info=template_info
        )
        print(f"✅ Results formatted successfully - {len(formatted_text)} characters")
        return formatted_text

    except Exception as e:
        print(f"❌ Error formatting results: {e}")
        return None


def categorize_with_llm(formatted_data: str):
    """Run LLM categorization on the formatted data."""
    print(f"\n🤖 Step 3: Running LLM Categorization")
    print("-" * 50)

    if not formatted_data:
        print("❌ No formatted data to categorize")
        return None

    try:
        results = categorize_procedures(formatted_data)
        print(
            f"✅ Categorization completed - {len(results.categorized_procedures)} procedures categorized"
        )
        return results

    except Exception as e:
        print(f"❌ Error in LLM categorization: {e}")
        return None


def display_results(results):
    """Display the categorization results."""
    print(f"\n📊 Step 4: Categorization Results")
    print("=" * 60)

    if not results or not results.categorized_procedures:
        print("❌ No results to display")
        return

    # Display categorized procedures
    print(f"\n🏥 CATEGORIZED PROCEDURES ({len(results.categorized_procedures)} total):")
    print("-" * 60)

    for i, proc in enumerate(results.categorized_procedures, 1):
        print(
            f"\n{i}. {proc.procedure_code} - {proc.complexity_category.upper()} COMPLEXITY"
        )
        print(f"   Description: {proc.procedure_description}")
        print(f"   Visit Volume: {proc.visit_volume:,}")
        print(f"   Confidence: {proc.confidence_score:.2f}")
        if proc.rationale:
            print("   Rationale:")
            for reason in proc.rationale:
                print(f"     • {reason}")

    # Display category distribution
    print(f"\n📈 COMPLEXITY DISTRIBUTION:")
    print("-" * 30)
    for category, count in results.category_distribution.items():
        percentage = (count / len(results.categorized_procedures)) * 100
        print(f"   {category:8}: {count:2} procedures ({percentage:5.1f}%)")

    # Display key insights
    if results.analysis_insights:
        print(f"\n💡 KEY INSIGHTS:")
        print("-" * 20)
        for insight in results.analysis_insights:
            print(f"   • {insight}")

    print(f"\n✨ Overall Confidence: {results.overall_confidence:.2f}")


def run_complete_workflow():
    """Execute the complete workflow from SQL to categorization."""
    print("🚀 PROCEDURE CODE CATEGORIZATION WORKFLOW")
    print("=" * 60)

    # Step 1: Run SQL query
    df = run_sql_query()
    if df is None or df.empty:
        print("❌ Workflow failed at SQL query step")
        return

    # Step 2: Format for LLM
    formatted_data = format_for_llm(df)
    if not formatted_data:
        print("❌ Workflow failed at formatting step")
        return

    # Step 3: Run LLM categorization
    results = categorize_with_llm(formatted_data)
    if not results:
        print("❌ Workflow failed at categorization step")
        return

    # Step 4: Display results
    display_results(results)

    print(f"\n🎉 WORKFLOW COMPLETED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    # Configure pandas display
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", None)
    pd.set_option("display.max_colwidth", 50)

    # Run the complete workflow
    run_complete_workflow()

    print(f"\n💡 CONFIGURATION:")
    print(f"   - Template: {TEMPLATE_ID}")
    print(f"   - Limit: {PARAMETERS['limit']} procedures")
    print(
        f"   - Modify these values at the top of the script to customize the analysis"
    )
