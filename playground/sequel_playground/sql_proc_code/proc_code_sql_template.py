"""
SQL Templates for Procedure Code Analysis

This module contains SQL templates for analyzing procedure codes, their types,
and related statistics.
"""

from dataclasses import dataclass
from typing import List


@dataclass
class SQLTemplate:
    id: str
    name: str
    description: str
    sql: str
    required_params: List[str]
    optional_params: List[str]
    output_columns: List[str]
    intent_keywords: List[str]


PROC_CODE_TEMPLATES = {
    "surgical_cardio_procedures": SQLTemplate(
        id="surgical_cardio_procedures",
        name="Surgical Cardio Procedures",
        description="Shows all surgical procedures related to cardiology",
        sql="""
        SELECT 
            "Procedure Code",
            "Procedure Code Description",
            "Procedure Sub Type",
            "Procedure Type",
            "Visits"
        FROM public.proc_codes
        WHERE "Procedure Type" = 'Surgical'
            AND "Procedure Sub Type" ILIKE '%Cardio%'
        ORDER BY "Visits" DESC
        LIMIT :limit;
        """,
        required_params=["limit"],
        optional_params=[],
        output_columns=[
            "Procedure Code",
            "Procedure Code Description",
            "Procedure Sub Type",
            "Procedure Type",
            "Visits",
        ],
        intent_keywords=["surgical", "cardio", "procedures", "CPT codes"],
    ),
    "procedure_type_distribution": SQLTemplate(
        id="procedure_type_distribution",
        name="Procedure Type Distribution",
        description="Shows the distribution of procedures across different types",
        sql="""
        SELECT 
            "Procedure Type",
            COUNT(*) as procedure_count,
            SUM("Visits") as total_visits
        FROM public.proc_codes
        GROUP BY "Procedure Type"
        ORDER BY procedure_count DESC;
        """,
        required_params=[],
        optional_params=[],
        output_columns=["Procedure Type", "procedure_count", "total_visits"],
        intent_keywords=["distribution", "types", "count", "visits"],
    ),
}
