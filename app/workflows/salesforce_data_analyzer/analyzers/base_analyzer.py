"""
Base Analyzer Class

This module defines the abstract base class for all Salesforce data analyzers.
Each analyzer combines SQL query execution with data structuring for specific use cases.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Type
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging


class BaseAnalyzer(ABC):
    """
    Abstract base class for Salesforce data analyzers.

    Each analyzer combines:
    1. SQL query definition
    2. Data structuring logic
    3. Output schema validation
    """

    def __init__(self, debug_mode: bool = False):
        self.debug_mode = debug_mode
        self.logger = logging.getLogger(self.__class__.__name__)

    @property
    @abstractmethod
    def analyzer_name(self) -> str:
        """Return the name of this analyzer."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Return a description of what this analyzer does."""
        pass

    @abstractmethod
    def get_sql_query(self) -> str:
        """
        Return the SQL query string for this analyzer.

        The query should use named parameters like :user_id, :start_date, :end_date
        that will be provided at runtime.

        Returns:
            SQL query string with named parameters
        """
        pass

    @abstractmethod
    def structure_data(
        self, raw_data: List[Dict[str, Any]], query_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Transform raw SQL results into structured data for LLM consumption.

        Args:
            raw_data: Raw results from SQL query execution
            query_params: Parameters used in the SQL query

        Returns:
            Structured data dictionary ready for LLM analysis
        """
        pass

    @abstractmethod
    def get_output_schema(self) -> Type[BaseModel]:
        """
        Return the Pydantic model that defines the expected output schema.

        Returns:
            Pydantic model class for output validation
        """
        pass

    def execute_and_structure(
        self, db_session: Session, query_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute the SQL query and structure the results.

        This is the main entry point that combines query execution with data structuring.

        Args:
            db_session: Database session for query execution
            query_params: Parameters for the SQL query

        Returns:
            Structured data ready for LLM consumption
        """
        try:
            # Get the SQL query
            sql_query = self.get_sql_query()

            if self.debug_mode:
                self.logger.info(f"Executing query for {self.analyzer_name}")
                self.logger.info(f"Parameters: {query_params}")

            # Execute the query
            raw_data = self._execute_query(db_session, sql_query, query_params)

            if self.debug_mode:
                self.logger.info(f"Retrieved {len(raw_data)} raw records")

            # Structure the data
            structured_data = self.structure_data(raw_data, query_params)

            if self.debug_mode:
                self.logger.info(f"Data structured successfully")

            # Add metadata
            structured_data["_metadata"] = {
                "analyzer": self.analyzer_name,
                "description": self.description,
                "raw_record_count": len(raw_data),
                "query_params": query_params,
            }

            return structured_data

        except Exception as e:
            self.logger.error(f"Error in {self.analyzer_name}: {str(e)}")
            raise

    def _execute_query(
        self, db_session: Session, query: str, params: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Execute a SQL query and return results as a list of dictionaries.

        Args:
            db_session: Database session
            query: SQL query string
            params: Query parameters

        Returns:
            List of dictionaries containing query results
        """
        try:
            result = db_session.execute(text(query), params)
            columns = result.keys()
            rows = result.fetchall()

            # Convert to list of dictionaries with proper type handling
            return [self._convert_row_to_dict(row, columns) for row in rows]

        except Exception as e:
            self.logger.error(f"Error executing query: {str(e)}")
            raise

    def _convert_row_to_dict(self, row, columns) -> Dict[str, Any]:
        """
        Convert a database row to a dictionary with proper type handling.

        Args:
            row: Database row
            columns: Column names

        Returns:
            Dictionary representation of the row
        """
        from datetime import datetime, date
        from uuid import UUID

        result = {}
        for i, column in enumerate(columns):
            value = row[i]

            # Handle special types
            if isinstance(value, (datetime, date)):
                result[column] = value.isoformat()
            elif isinstance(value, UUID):
                result[column] = str(value)
            elif value is None:
                result[column] = None
            else:
                result[column] = value

        return result

    def validate_output(self, structured_data: Dict[str, Any]) -> bool:
        """
        Validate the structured data against the output schema.

        Args:
            structured_data: Data to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            output_schema = self.get_output_schema()
            output_schema(**structured_data)
            return True
        except Exception as e:
            self.logger.error(f"Output validation failed: {str(e)}")
            return False

    def get_required_parameters(self) -> List[str]:
        """
        Return the list of required parameters for this analyzer.

        Override this method if your analyzer needs specific parameters.

        Returns:
            List of required parameter names
        """
        return ["user_id", "start_date", "end_date"]

    def export_debug_data(
        self, structured_data: Dict[str, Any], export_path: str
    ) -> None:
        """
        Export structured data for debugging purposes.

        Args:
            structured_data: Data to export
            export_path: Path to export the data to
        """
        import json
        from pathlib import Path

        try:
            Path(export_path).parent.mkdir(parents=True, exist_ok=True)

            with open(export_path, "w") as f:
                json.dump(structured_data, f, indent=2, default=str)

            self.logger.info(f"Debug data exported to: {export_path}")

        except Exception as e:
            self.logger.error(f"Error exporting debug data: {str(e)}")
