#!/usr/bin/env python3
"""
Test Script for SQL Queries

This script directly tests the SQL queries from sql_templates.py
to help debug and verify the results.
"""

import os
import sys
from datetime import datetime, date, timedelta
from pprint import pprint

# Add the project root to the Python path
project_root = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.insert(0, project_root)

from sqlalchemy import text
from app.database.session import SessionLocal
from app.workflows.monthly_activity_summary_nodes.sql_templates import (
    MonthlyActivitySQLTemplates,
)


def test_sql_queries():
    """Test each SQL query template with sample data."""

    print("🔍 Testing SQL Queries")
    print("=" * 60)

    # Create database session
    db = SessionLocal()

    try:
        # Test parameters
        test_user_id = "005UJ000002LyknYAC"  # Replace with a real Salesforce user ID
        end_date = date.today()
        start_date = end_date - timedelta(days=30)

        print(f"📋 Test Parameters:")
        print(f"   User ID: {test_user_id}")
        print(f"   Date Range: {start_date} to {end_date}")
        print()

        # Test each query template
        queries = {
            "Monthly Activities": MonthlyActivitySQLTemplates.get_monthly_activities_query(),
            "Individual Activities": MonthlyActivitySQLTemplates.get_individual_activities_query(),
            "Activity Summary Stats": MonthlyActivitySQLTemplates.get_activity_summary_stats_query(),
            "Specialty Breakdown": MonthlyActivitySQLTemplates.get_specialty_breakdown_query(),
            "Contact Activity Summary": MonthlyActivitySQLTemplates.get_contact_activity_summary_query(),
        }

        for query_name, query in queries.items():
            print(f"🔎 Testing {query_name} Query:")
            try:
                # Execute query with parameters
                result = db.execute(
                    text(query),
                    {
                        "user_id": test_user_id,
                        "start_date": start_date,
                        "end_date": end_date,
                    },
                )

                # Fetch results
                rows = result.fetchall()

                print(f"   ✅ Query executed successfully!")
                print(f"   📊 Results count: {len(rows)}")

                # Display sample results
                if rows:
                    print("   📝 Sample row:")
                    sample_row = rows[0]
                    # Convert row to dict for better display
                    row_dict = dict(zip(result.keys(), sample_row))
                    pprint(row_dict, indent=8)
                else:
                    print("   ⚠️  No results found")

            except Exception as e:
                print(f"   ❌ Query failed:")
                print(f"   Error: {str(e)}")

            print()

    finally:
        db.close()


def main():
    """Main test function."""
    print("🧪 SQL Query Test Suite")
    print("=" * 80)
    print()

    print("⚠️  Note: This test requires:")
    print("   1. A valid database connection")
    print("   2. Salesforce data in the database")
    print("   3. A valid Salesforce user ID with activity data")
    print()

    # Run the SQL query tests directly
    test_sql_queries()


if __name__ == "__main__":
    main()
