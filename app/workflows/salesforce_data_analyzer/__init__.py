"""
Salesforce Data Analyzer Workflow

A modular, dynamic workflow system for analyzing Salesforce data with proper
handling of complex relationships between Activities and Contacts.

Key Features:
- Handles multiple contacts per activity through TaskWhoRelation table
- Modular analyzer pattern for different analysis types
- Combined SQL + Data Structuring in single components
- Extensible registry system for new analyzer types
"""

from .salesforce_data_analyzer_workflow import SalesforceDataAnalyzerWorkflow
from .analyzers import BaseAnalyzer, MonthlyActivitySummaryAnalyzer
from .nodes import UnifiedSQLDataNode, RequestCategoryNode

__all__ = [
    "SalesforceDataAnalyzerWorkflow",
    "BaseAnalyzer",
    "MonthlyActivitySummaryAnalyzer",
    "UnifiedSQLDataNode",
    "RequestCategoryNode",
]
