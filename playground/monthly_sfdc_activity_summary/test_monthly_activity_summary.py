#!/usr/bin/env python3
"""
Test Script for Monthly Activity Summary Workflow

This script tests the monthly activity summary workflow with sample data
to ensure all components are working correctly.
"""

import os
import sys
import json
from datetime import datetime, date, timedelta
from pprint import pprint

# Add the project root to the Python path (go up two levels from playground/monthly_sfdc_activity_summary/)
project_root = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.insert(0, project_root)

from app.workflows.monthly_activity_summary_workflow import (
    MonthlyActivitySummaryWorkflow,
)


def test_workflow_with_sample_data():
    """Test the workflow with sample event data."""

    print("🧪 Testing Monthly Activity Summary Workflow")
    print("=" * 60)

    # Create test event data
    # Note: You'll need to replace this with a real Salesforce user ID from your database
    test_user_id = "0051234567890123"  # Replace with actual Salesforce user ID

    # Test event with date range (past 30 days)
    end_date = date.today()
    start_date = end_date - timedelta(days=30)

    test_event = {
        "user_id": test_user_id,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "request_type": "monthly_summary",
        "session_id": f"test_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "metadata": {"source": "test_script", "test_run": True},
    }

    print(f"📋 Test Event Data:")
    print(f"   User ID: {test_event['user_id']}")
    print(f"   Date Range: {test_event['start_date']} to {test_event['end_date']}")
    print(f"   Request Type: {test_event['request_type']}")
    print()

    try:
        print("🚀 Running workflow...")
        result = MonthlyActivitySummaryWorkflow.process(test_event)

        print("✅ Workflow completed successfully!")
        print()

        # Display key results
        print("📊 Workflow Results Summary:")
        print(f"   Success: {result.get('success', False)}")
        print(f"   User ID: {result.get('user_id', 'N/A')}")
        print(f"   Workflow Type: {result.get('workflow_type', 'N/A')}")
        print()

        # Display data metrics
        data_metrics = result.get("data_metrics", {})
        print("📈 Data Metrics:")
        print(f"   Total Activities: {data_metrics.get('total_activities', 0)}")
        print(f"   Activities Retrieved: {data_metrics.get('activities_retrieved', 0)}")
        print(f"   Specialties Covered: {data_metrics.get('specialties_covered', 0)}")
        print(f"   Contacts Engaged: {data_metrics.get('contacts_engaged', 0)}")
        print()

        # Display processing metadata
        processing_metadata = result.get("processing_metadata", {})
        print("⚙️ Processing Metadata:")
        print(
            f"   Request Categorized: {processing_metadata.get('request_categorized', False)}"
        )
        print(
            f"   SQL Data Retrieved: {processing_metadata.get('sql_data_retrieved', False)}"
        )
        print(
            f"   Data Structured: {processing_metadata.get('data_structured', False)}"
        )
        print(
            f"   LLM Summary Generated: {processing_metadata.get('llm_summary_generated', False)}"
        )
        print(
            f"   Total Processing Nodes: {processing_metadata.get('total_processing_nodes', 0)}"
        )

        errors = processing_metadata.get("errors", [])
        if errors:
            print(f"   Errors: {len([e for e in errors if e])}")
            for error in errors:
                if error:
                    print(f"     - {error}")
        else:
            print("   Errors: None")
        print()

        # Display summary preview
        summary = result.get("summary", {})
        if summary.get("executive_summary"):
            print("📄 Executive Summary Preview:")
            exec_summary = summary.get("executive_summary", "")[:200]
            print(f"   {exec_summary}...")
            print()

        # Display specialty highlights count
        specialty_highlights = summary.get("key_highlights_by_specialty", {})
        if specialty_highlights:
            print(
                f"🏥 Specialty Highlights: {len(specialty_highlights)} specialties analyzed"
            )
            for specialty in list(specialty_highlights.keys())[:3]:  # Show first 3
                print(f"   - {specialty}")
            if len(specialty_highlights) > 3:
                print(f"   ... and {len(specialty_highlights) - 3} more")
            print()

        # Display recommendations count
        recommendations = summary.get("strategic_recommendations", [])
        if recommendations:
            print(f"💡 Strategic Recommendations: {len(recommendations)} generated")
            if recommendations:
                print(f"   Example: {recommendations[0][:100]}...")
            print()

        # Save full results to file for detailed review
        output_file = f"monthly_summary_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        output_path = os.path.join(os.path.dirname(__file__), output_file)
        with open(output_path, "w") as f:
            json.dump(result, f, indent=2, default=str)

        print(f"💾 Full results saved to: {output_path}")
        print()
        print("🎉 Test completed successfully!")

        return result

    except Exception as e:
        print(f"❌ Workflow failed with error: {str(e)}")
        print(f"   Error type: {type(e).__name__}")
        import traceback

        print(f"   Traceback:")
        traceback.print_exc()
        return None


def test_workflow_validation():
    """Test workflow schema validation."""

    print("🔍 Testing Workflow Schema Validation")
    print("=" * 60)

    try:
        # Test with invalid data
        invalid_event = {
            "user_id": "invalid_id",  # Too short
            "request_type": "invalid_type",
        }

        print("Testing with invalid event data...")
        result = MonthlyActivitySummaryWorkflow.process(invalid_event)
        print("❌ Validation should have failed but didn't")

    except Exception as e:
        print(f"✅ Validation correctly failed: {str(e)}")

    try:
        # Test with valid data
        valid_event = MonthlyActivitySummaryWorkflow.create_test_event(
            user_id="0051234567890123", start_date="2024-01-01", end_date="2024-01-31"
        )

        print("Testing with valid event data structure...")
        # Just test instantiation, not full execution
        workflow = MonthlyActivitySummaryWorkflow()
        print("✅ Workflow instantiation successful")

    except Exception as e:
        print(f"❌ Validation failed unexpectedly: {str(e)}")


def main():
    """Main test function."""

    print("🧪 Monthly Activity Summary Workflow Test Suite")
    print("=" * 80)
    print()

    # Test 1: Schema validation
    test_workflow_validation()
    print()

    # Test 2: Full workflow execution
    print("⚠️  Note: The following test requires:")
    print("   1. A valid database connection")
    print("   2. Salesforce data in the database")
    print("   3. A valid Salesforce user ID with activity data")
    print("   4. OpenAI API key configured")
    print()

    user_input = input("Do you want to run the full workflow test? (y/N): ")
    if user_input.lower() in ["y", "yes"]:
        print()
        test_workflow_with_sample_data()
    else:
        print("Skipping full workflow test.")

    print()
    print("🏁 Test suite completed!")


if __name__ == "__main__":
    main()
