#!/usr/bin/env python3
"""
Run and Export - Simplest Approach

Just run the normal workflow and then export the debug data.
No workflow modifications needed.
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
from export_debug_data import export_all_debug_data


def main(user_id: str = "005UJ000002LyknYAC", days_back: int = 30):
    """
    Super simple approach: Run workflow normally, then export debug data.
    """
    print("🚀 Running Monthly Activity Summary + Export")
    print("=" * 50)

    # 1. Create event (normal workflow usage)
    end_date = date.today()
    start_date = end_date - timedelta(days=days_back)

    event = MonthlyActivitySummaryEvent(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        request_type="monthly_summary",
    )

    print(f"📅 User: {user_id}")
    print(f"📅 Period: {start_date} to {end_date}")
    print()

    # 2. Run workflow (normal usage)
    print("⚙️  Running workflow...")
    workflow = MonthlyActivitySummaryWorkflow()
    result = workflow.run(event.model_dump())

    # 3. Check if successful
    workflow_success = True
    for node_name, node_result in result.nodes.items():
        if node_result.get("error"):
            workflow_success = False
            print(f"❌ Error in {node_name}: {node_result.get('error')}")

    if not workflow_success:
        print("❌ Workflow failed, cannot export data")
        return

    print("✅ Workflow completed successfully!")
    print(f"📊 Retrieved {result.metadata.get('activity_count', 0)} activities")
    print()

    # 4. Export debug data (this is the magic!)
    print("📁 Exporting debug data...")
    exported_files = export_all_debug_data(result, user_id)

    print()
    print("🎉 Complete! You now have:")
    print(f"  📄 Structured Data: {exported_files['structured_data']}")
    print(f"  📄 Actual LLM Prompt: {exported_files['actual_llm_prompt']}")
    print()
    print("💡 These files show you exactly what data structure was sent to the LLM!")
    print(
        "🔍 The prompt file contains the ACTUAL prompts sent to OpenAI, not reconstructed ones!"
    )


if __name__ == "__main__":
    main()
