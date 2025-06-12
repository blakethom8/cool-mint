"""
SQL Result Formatter for LLM Context

This module provides functions to format SQL query results into structured text
that can be effectively used as context for large language model queries.
"""

from typing import Dict, Any, List
import pandas as pd
from datetime import datetime


def format_top_providers_result(df: pd.DataFrame, template_info: Dict) -> str:
    """
    Format top providers by specialty results into LLM-friendly text.

    Args:
        df: DataFrame containing the query results
        template_info: Dictionary containing metadata about the query template

    Returns:
        Formatted string ready for LLM context
    """
    if df.empty:
        return "No provider data found for the specified specialty."

    # Start with the analysis context
    formatted_text = [
        f"Analysis Type: {template_info['name']}",
        f"Analysis Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Total Providers Analyzed: {len(df)}",
        "\nKey Statistics:",
        f"- Total Visit Volume: {df['total_visits'].sum():,}",
        f"- Average Visits per Provider: {df['total_visits'].mean():,.1f}",
        f"- Number of Organizations: {df['primary_organization'].nunique()}",
        f"- Number of Practice Locations: {df['primary_practice_name'].nunique()}",
        "\nDetailed Provider Analysis:",
    ]

    # Group by specialty for structured analysis
    for specialty, group in df.groupby("primary_specialty"):
        formatted_text.extend(
            [
                f"\nSpecialty: {specialty}",
                f"Number of Providers: {len(group)}",
                "Top Providers:",
            ]
        )

        # Add individual provider details
        for _, row in group.iterrows():
            provider_text = (
                f"- Dr. {row['first_name']} {row['last_name']}\n"
                f"  * Organization: {row['primary_organization']}\n"
                f"  * Practice: {row['primary_practice_name']}\n"
                f"  * Total Visits: {row['total_visits']:,}"
            )
            formatted_text.append(provider_text)

    return "\n".join(formatted_text)


def format_top_organizations_result(df: pd.DataFrame, template_info: Dict) -> str:
    """
    Format top organizations by specialty results into LLM-friendly text.

    Args:
        df: DataFrame containing the query results
        template_info: Dictionary containing metadata about the query template

    Returns:
        Formatted string ready for LLM context
    """
    if df.empty:
        return "No organization data found for the specified specialty."

    # Start with the analysis context
    formatted_text = [
        f"Analysis Type: {template_info['name']}",
        f"Analysis Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Total Organizations Analyzed: {len(df)}",
        "\nKey Statistics:",
        f"- Total Provider Count: {df['provider_count'].sum():,}",
        f"- Average Providers per Organization: {df['provider_count'].mean():,.1f}",
        "\nDetailed Organization Analysis:",
    ]

    # Group by specialty for structured analysis
    for specialty, group in df.groupby("primary_specialty"):
        formatted_text.extend(
            [
                f"\nSpecialty: {specialty}",
                f"Number of Organizations: {len(group)}",
                "Market Leaders:",
            ]
        )

        # Add individual organization details
        for _, row in group.iterrows():
            org_text = (
                f"- {row['primary_organization']}\n"
                f"  * Provider Count: {row['provider_count']:,}\n"
                f"  * Market Position: Rank {_ + 1}"
            )
            formatted_text.append(org_text)

    return "\n".join(formatted_text)


def format_procedure_codes_result(df: pd.DataFrame, template_info: Dict) -> str:
    """
    Format procedure codes results into LLM-friendly text for categorization.

    Args:
        df: DataFrame containing procedure code results
        template_info: Dictionary containing metadata about the query template

    Returns:
        Formatted string ready for LLM categorization
    """
    if df.empty:
        return "No procedure code data found."

    # Start with the analysis context
    formatted_text = [
        f"Analysis Type: {template_info['name']}",
        f"Analysis Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Total Procedures Analyzed: {len(df)}",
        "\nProcedure Summary:",
        f"- Total Visit Volume: {df['Visits'].sum():,}",
        f"- Average Visits per Procedure: {df['Visits'].mean():,.1f}",
        f"- Procedure Types: {df['Procedure Type'].nunique()}",
        f"- Procedure Sub Types: {df['Procedure Sub Type'].nunique()}",
        "\nDetailed Procedure Analysis:",
    ]

    # Add individual procedure details for categorization
    for idx, row in df.iterrows():
        procedure_text = (
            f"\nProcedure {idx + 1}:"
            f"\n- Code: {row['Procedure Code']}"
            f"\n- Description: {row['Procedure Code Description']}"
            f"\n- Type: {row['Procedure Type']}"
            f"\n- Sub Type: {row['Procedure Sub Type']}"
            f"\n- Visit Volume: {row['Visits']:,}"
        )
        formatted_text.append(procedure_text)

    return "\n".join(formatted_text)


def format_sql_result_for_llm(
    df: pd.DataFrame, template_id: str, template_info: Dict[str, Any]
) -> str:
    """
    Main entry point for formatting SQL results into LLM-friendly text.

    Args:
        df: DataFrame containing the query results
        template_id: Identifier for the SQL template used
        template_info: Dictionary containing metadata about the query template

    Returns:
        Formatted string ready for LLM context
    """
    formatters = {
        "top_providers_by_specialty": format_top_providers_result,
        "top_organizations_by_specialty": format_top_organizations_result,
        "surgical_cardio_procedures": format_procedure_codes_result,
    }

    formatter = formatters.get(template_id)
    if formatter is None:
        return f"No formatter available for template: {template_id}"

    return formatter(df, template_info)


# Example usage:
"""
# Get your SQL results as a DataFrame
df = run_sql_query()  # Your SQL execution function

# Get template info from SQL_TEMPLATES
template_id = 'top_providers_by_specialty'
template_info = SQL_TEMPLATES[template_id]

# Format the results
formatted_text = format_sql_result_for_llm(
    df=df,
    template_id=template_id,
    template_info=template_info
)

# Use in LLM context
llm_context = f'''
Please analyze the following healthcare market data:

{formatted_text}

Question: What are the key insights from this data?
'''
"""
