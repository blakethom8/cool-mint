#!/usr/bin/env python3
"""
Quick Analysis Example

This script demonstrates how to analyze your Monthly Activity Summary data pipeline.
"""

import sys
import os
from datetime import datetime, date, timedelta

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.schemas.monthly_activity_summary_schema import MonthlyActivitySummaryEvent
from app.workflows.monthly_activity_summary_workflow import (
    MonthlyActivitySummaryWorkflow,
)


def quick_analysis_example():
    """
    Quick example showing how to analyze your data pipeline.
    """
    print("🔍 Monthly Activity Summary - Data Pipeline Analysis Example")
    print("=" * 60)

    # 1. Create a test event (adjust user_id to match your data)
    user_id = "005UJ000002LyknYAC"  # Replace with your actual user ID
    end_date = date.today()
    start_date = end_date - timedelta(days=30)

    event = MonthlyActivitySummaryEvent(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        request_type="monthly_summary",
        metadata={"analysis_example": True},
    )

    print(f"📅 Analyzing data for user: {user_id}")
    print(f"📅 Date range: {start_date} to {end_date}")
    print()

    # 2. Run workflow with debug and export options
    print("🚀 Running workflow with analysis options...")

    workflow = MonthlyActivitySummaryWorkflow(
        debug_mode=True,  # Enable detailed logging
        export_data=True,  # Export structured data to files
        export_prompts=True,  # Export LLM prompts to files
    )

    try:
        # Convert event object to dictionary for the workflow
        event_dict = event.model_dump()
        result = workflow.run(event_dict)

        # Check if workflow completed successfully by looking at node results
        workflow_success = True
        errors = []

        for node_name, node_result in result.nodes.items():
            if node_result.get("error"):
                workflow_success = False
                errors.append(f"{node_name}: {node_result.get('error')}")

        if workflow_success:
            print("✅ Analysis completed successfully!")
            print()

            # 3. Show what was analyzed
            print("📊 Analysis Results:")
            print(
                f"  - Activities retrieved: {result.metadata.get('activity_count', 'Unknown')}"
            )
            print(
                f"  - Data structured: {result.metadata.get('data_structured', 'Unknown')}"
            )
            print(
                f"  - LLM analysis: {result.metadata.get('llm_summary_generated', 'Unknown')}"
            )
            print()

            # 4. Show where files were exported
            print("📁 Files exported to:")
            print(
                "  - exports/structured_data/ - Complete structured data in JSON format"
            )
            print("  - exports/llm_prompts/ - Complete LLM prompts and analysis")
            print("  - analysis.log - Detailed debug logs")
            print()

            # 5. Show sample of results
            llm_result = result.nodes.get("LLMSummaryNode", {}).get("result")
            if llm_result and hasattr(llm_result, "executive_summary"):
                print("📝 Sample of Executive Summary:")
                summary = llm_result.executive_summary
                print(f"  {summary[:200]}...")
                print()

            print("💡 What to do next:")
            print(
                "  1. Check the exported JSON files to understand your data structure"
            )
            print("  2. Review the LLM prompts to see what's being analyzed")
            print("  3. Look at the debug logs for detailed processing information")
            print("  4. Use the analysis script for more detailed investigation:")
            print(
                "     python analyze_data_pipeline.py --debug --export-data --export-prompts"
            )

        else:
            print("❌ Analysis failed")
            for error in errors:
                print(f"  Error: {error}")

    except Exception as e:
        print(f"❌ Error running analysis: {str(e)}")
        print()
        print("💡 Troubleshooting tips:")
        print("  1. Make sure your database connection is working")
        print("  2. Verify the user_id exists in your database")
        print("  3. Check if there are activities in the date range")
        print("  4. Review the logs for more details")


if __name__ == "__main__":
    quick_analysis_example()
