#!/usr/bin/env python3
"""
Test Script for New Salesforce Data Analyzer Workflow

This script tests the new modular workflow that properly handles multiple contacts
per activity through the TaskWhoRelation table.
"""

import sys
import os
from datetime import datetime, date, timedelta
from pprint import pprint

# Add the project root to the Python path
project_root = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.insert(0, project_root)

from app.workflows.salesforce_data_analyzer import SalesforceDataAnalyzerWorkflow


def test_new_workflow():
    """Test the new Salesforce Data Analyzer workflow."""

    print("🧪 Testing New Salesforce Data Analyzer Workflow")
    print("=" * 80)

    # Create workflow instance
    workflow = SalesforceDataAnalyzerWorkflow(debug_mode=True, export_debug_data=True)

    print("📋 Workflow Metadata:")
    metadata = workflow.export_workflow_metadata()
    pprint(metadata, indent=2)
    print()

    print("🔍 Available Analyzers:")
    analyzers = workflow.get_available_analyzers()
    for name, description in analyzers.items():
        print(f"  - {name}: {description}")
    print()

    # Test parameters
    test_user_id = "005UJ000002LyknYAC"  # Replace with a real Salesforce user ID
    end_date = date.today()
    start_date = end_date - timedelta(days=30)

    # Create event data
    event_data = {
        "user_id": test_user_id,
        "start_date": start_date,
        "end_date": end_date,
        "request_type": "monthly_activity_summary",
    }

    print(f"📅 Test Parameters:")
    print(f"   User ID: {test_user_id}")
    print(f"   Date Range: {start_date} to {end_date}")
    print(f"   Request Type: {event_data['request_type']}")
    print()

    # Validate event
    print("✅ Validating event data...")
    is_valid, error_message = workflow.validate_event(event_data)
    if not is_valid:
        print(f"❌ Event validation failed: {error_message}")
        return
    print("✅ Event validation passed!")
    print()

    # Run workflow
    print("🚀 Running workflow...")
    try:
        result = workflow.run(event_data)

        # Check if workflow was successful
        if result.metadata.get("workflow_success", False):
            print("✅ Workflow completed successfully!")

            # Display results summary
            print("\n📊 Results Summary:")
            print(
                f"   Analyzer Used: {result.metadata.get('analyzer_name', 'Unknown')}"
            )
            print(f"   Raw Records: {result.metadata.get('raw_record_count', 0)}")

            # Get structured data
            structured_data = result.nodes.get("UnifiedSQLDataNode", {}).get(
                "result", {}
            )
            if structured_data:
                basic_metrics = structured_data.get("basic_metrics", {})
                print(
                    f"   Total Activities: {basic_metrics.get('total_activities', 0)}"
                )
                print(f"   Unique Contacts: {basic_metrics.get('unique_contacts', 0)}")
                print(
                    f"   Unique Organizations: {basic_metrics.get('unique_organizations', 0)}"
                )
                print(
                    f"   Activities with Contacts: {basic_metrics.get('activities_with_contacts', 0)}"
                )
                print(
                    f"   Activities without Contacts: {basic_metrics.get('activities_without_contacts', 0)}"
                )
                print(
                    f"   Total Contact Relationships: {basic_metrics.get('total_contact_relationships', 0)}"
                )

                # Show sample activity with contacts
                activities = structured_data.get("activities", [])
                print(f"\n🔍 Sample Activity Analysis:")
                sample_activity = None
                for activity in activities:
                    if activity.get("contacts"):
                        sample_activity = activity
                        break

                if sample_activity:
                    print(f"   Activity ID: {sample_activity.get('activity_id')}")
                    print(f"   Subject: {sample_activity.get('subject')}")
                    print(f"   Date: {sample_activity.get('activity_date')}")
                    print(
                        f"   Number of Contacts: {len(sample_activity.get('contacts', []))}"
                    )

                    contacts = sample_activity.get("contacts", [])
                    for i, contact in enumerate(
                        contacts[:3], 1
                    ):  # Show first 3 contacts
                        print(
                            f"     Contact {i}: {contact.get('contact_name')} ({contact.get('specialty', 'Unknown')})"
                        )

                    if len(contacts) > 3:
                        print(f"     ... and {len(contacts) - 3} more contacts")
                else:
                    print("   No activities with contacts found")

                # Show specialty distribution
                specialty_dist = structured_data.get("specialty_distribution", {})
                if specialty_dist:
                    print(f"\n📈 Top Specialties:")
                    for specialty, count in list(specialty_dist.items())[:5]:
                        print(f"   {specialty}: {count} activities")

        else:
            print("❌ Workflow failed!")
            error = result.metadata.get("workflow_error", "Unknown error")
            print(f"   Error: {error}")

            # Show node errors
            for node_name, node_result in result.nodes.items():
                if node_result.get("error"):
                    print(f"   {node_name} Error: {node_result.get('error')}")

    except Exception as e:
        print(f"❌ Exception during workflow execution: {str(e)}")
        import traceback

        traceback.print_exc()


def test_analyzer_directly():
    """Test the analyzer directly without the workflow."""

    print("\n🔬 Testing Monthly Activity Summary Analyzer Directly")
    print("=" * 80)

    from app.workflows.salesforce_data_analyzer.analyzers import (
        MonthlyActivitySummaryAnalyzer,
    )
    from app.database.session import SessionLocal
    from datetime import timedelta

    # Create analyzer
    analyzer = MonthlyActivitySummaryAnalyzer(debug_mode=True)

    print(f"📋 Analyzer: {analyzer.analyzer_name}")
    print(f"📋 Description: {analyzer.description}")
    print()

    # Test parameters
    test_user_id = "005UJ000002LyknYAC"
    end_date = date.today()
    start_date = end_date - timedelta(days=30)

    query_params = {
        "user_id": test_user_id,
        "start_date": start_date,
        "end_date": end_date,
    }

    print(f"📅 Query Parameters: {query_params}")
    print()

    # Test SQL query
    print("🔍 SQL Query:")
    sql_query = analyzer.get_sql_query()
    print(sql_query[:500] + "..." if len(sql_query) > 500 else sql_query)
    print()

    # Execute analyzer
    print("⚙️ Executing analyzer...")
    try:
        db_session = SessionLocal()
        try:
            structured_data = analyzer.execute_and_structure(db_session, query_params)

            print("✅ Analyzer executed successfully!")
            print(
                f"📊 Raw Record Count: {structured_data.get('_metadata', {}).get('raw_record_count', 0)}"
            )

            # Validate output
            print("🔍 Validating output schema...")
            is_valid = analyzer.validate_output(structured_data)
            print(f"   Schema Valid: {is_valid}")

        finally:
            db_session.close()

    except Exception as e:
        print(f"❌ Analyzer execution failed: {str(e)}")
        import traceback

        traceback.print_exc()


def main():
    """Main test function."""
    print("🧪 Salesforce Data Analyzer - Test Suite")
    print("=" * 80)
    print()

    print("⚠️  Note: This test requires:")
    print("   1. A valid database connection")
    print("   2. Salesforce data in the database")
    print("   3. TaskWhoRelation data linking activities to contacts")
    print("   4. A valid Salesforce user ID with activity data")
    print()

    # Test the full workflow
    test_new_workflow()

    # Test the analyzer directly
    test_analyzer_directly()

    print("\n🎉 Testing completed!")


if __name__ == "__main__":
    main()
