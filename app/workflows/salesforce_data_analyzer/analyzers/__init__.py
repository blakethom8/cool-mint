"""
Salesforce Data Analyzers

This module contains analyzer classes that combine SQL queries with data structuring
for different types of Salesforce data analysis.
"""

from .base_analyzer import BaseAnalyzer
from .monthly_activity_summary_analyzer import MonthlyActivitySummaryAnalyzer

__all__ = ["BaseAnalyzer", "MonthlyActivitySummaryAnalyzer"]
