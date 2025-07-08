#!/usr/bin/env python3
"""
Export Debug Data - Simple Utility

Simple functions to export structured data and LLM prompts for analysis
without modifying the main workflow.
"""

import json
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.core.task import TaskContext


def export_structured_data(task_context: TaskContext, user_id: str = None) -> str:
    """
    Export structured data from a TaskContext to a JSON file.

    Args:
        task_context: TaskContext containing the workflow results
        user_id: Optional user ID for filename

    Returns:
        Path to the exported file
    """
    # Get structured data from DataStructureNode
    structured_data = task_context.nodes.get("DataStructureNode", {}).get("result")

    if not structured_data:
        print("❌ No structured data found in TaskContext")
        return None

    # Create exports directory
    export_dir = Path("exports/manual_export")
    export_dir.mkdir(parents=True, exist_ok=True)

    # Create filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    user_id = (
        user_id or task_context.event.user_id
        if hasattr(task_context.event, "user_id")
        else "unknown"
    )
    filename = f"structured_data_{user_id}_{timestamp}.json"
    filepath = export_dir / filename

    # Export data
    with open(filepath, "w") as f:
        json.dump(structured_data, f, indent=2, default=str)

    print(f"✅ Structured data exported to: {filepath}")

    # Also create a summary
    summary_filepath = export_dir / f"summary_{user_id}_{timestamp}.json"
    activities = structured_data.get("activities", [])

    summary = {
        "export_info": {
            "timestamp": timestamp,
            "user_id": user_id,
            "file_path": str(filepath),
        },
        "data_summary": {
            "total_activities": len(activities),
            "period": f"{structured_data.get('summary_period', {}).get('start_date')} to {structured_data.get('summary_period', {}).get('end_date')}",
            "basic_metrics": structured_data.get("basic_metrics", {}),
        },
        "sample_activities": activities[:3] if activities else [],
        "specialty_distribution": _get_specialty_distribution(activities),
    }

    with open(summary_filepath, "w") as f:
        json.dump(summary, f, indent=2, default=str)

    print(f"✅ Summary exported to: {summary_filepath}")
    return str(filepath)


def export_llm_prompt(task_context: TaskContext, user_id: str = None) -> str:
    """
    Export the ACTUAL LLM prompt that was sent during the workflow.

    This extracts the real prompts from the task context metadata.

    Args:
        task_context: TaskContext containing the workflow results
        user_id: Optional user ID for filename

    Returns:
        Path to the exported prompt file
    """
    # Get the actual LLM details from task context metadata
    llm_details = task_context.metadata.get("llm_details")

    if not llm_details:
        print("❌ No LLM details found in task context metadata")
        print(
            "💡 This means the actual prompts weren't captured during workflow execution"
        )
        return None

    # Create exports directory
    export_dir = Path("exports/manual_export")
    export_dir.mkdir(parents=True, exist_ok=True)

    # Create filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    user_id = (
        user_id or task_context.event.user_id
        if hasattr(task_context.event, "user_id")
        else "unknown"
    )
    filename = f"actual_llm_prompt_{user_id}_{timestamp}.txt"
    filepath = export_dir / filename

    # Get the actual prompts
    system_prompt = llm_details.get("system_prompt", "")
    user_prompt = llm_details.get("user_prompt", "")
    model_info = llm_details.get("model", {})

    # Export the ACTUAL prompt
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("=== ACTUAL LLM PROMPT ===\n")
        f.write("(This is the EXACT prompt that was sent to the LLM)\n\n")

        f.write("=== MODEL INFORMATION ===\n")
        f.write(f"Provider: {model_info.get('provider', 'Unknown')}\n")
        f.write(f"Model: {model_info.get('name', 'Unknown')}\n")
        f.write("\n")

        f.write("=== SYSTEM PROMPT ===\n")
        f.write(system_prompt)
        f.write("\n\n")

        f.write("=== USER PROMPT ===\n")
        f.write(user_prompt)
        f.write("\n")

    print(f"✅ ACTUAL LLM prompt exported to: {filepath}")
    return str(filepath)


def export_all_debug_data(
    task_context: TaskContext, user_id: str = None
) -> Dict[str, str]:
    """
    Export both structured data and LLM prompt.

    Args:
        task_context: TaskContext containing the workflow results
        user_id: Optional user ID for filename

    Returns:
        Dictionary with paths to exported files
    """
    print("🔍 Exporting all debug data...")

    structured_path = export_structured_data(task_context, user_id)
    prompt_path = export_llm_prompt(task_context, user_id)

    return {"structured_data": structured_path, "actual_llm_prompt": prompt_path}


def _get_specialty_distribution(activities) -> Dict[str, int]:
    """Get distribution of activities by specialty."""
    distribution = {}
    for activity in activities:
        specialty = activity.get("contact_info", {}).get("specialty", "Unknown")
        distribution[specialty] = distribution.get(specialty, 0) + 1
    return dict(sorted(distribution.items(), key=lambda x: x[1], reverse=True))


# Note: We no longer need to reconstruct the prompt since we can get the actual one from task context metadata!


# Simple usage example
def example_usage():
    """Example of how to use these export functions."""
    print("📖 Example Usage:")
    print("1. Run your normal workflow")
    print("2. Call export functions with the TaskContext result")
    print()
    print("Example code:")
    print("""
from export_debug_data import export_all_debug_data

# After running workflow
workflow = MonthlyActivitySummaryWorkflow()
result = workflow.run(event_dict)

# Export debug data
export_all_debug_data(result, user_id="your_user_id")
""")


if __name__ == "__main__":
    example_usage()
