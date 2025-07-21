"""
SQL Data Retrieval Node

This node executes SQL queries to retrieve activity data from the database
with proper joins to contacts and users tables.
"""

import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy import text
from sqlalchemy.orm import Session

from core.nodes.base import Node
from core.task import TaskContext
from database.session import SessionLocal
from workflows.monthly_activity_summary_nodes.sql_templates import (
    MonthlyActivitySQLTemplates,
)


class SQLDataNode(Node):
    """Node that retrieves activity data from the database using SQL queries."""

    def __init__(self):
        self.sql_templates = MonthlyActivitySQLTemplates()
        self.logger = logging.getLogger(__name__)

    def process(self, task_context: TaskContext) -> TaskContext:
        """
        Execute SQL queries to retrieve activity data.

        Args:
            task_context: Task context containing the event data

        Returns:
            Updated task context with retrieved data
        """
        try:
            # Extract parameters from event
            user_id = task_context.event.user_id
            start_date, end_date = self._get_date_range(task_context.event)

            self.logger.info(
                f"Retrieving activity data for user {user_id} from {start_date} to {end_date}"
            )

            # Get database session
            db_session = SessionLocal()

            try:
                # Execute all required queries
                query_params = {
                    "user_id": user_id,
                    "start_date": start_date,
                    "end_date": end_date,
                }

                # Get individual activities with complete contact context
                activities_data = self._execute_query(
                    db_session,
                    self.sql_templates.get_individual_activities_query(),
                    query_params,
                )

                # Optional: Get basic summary stats for workflow metadata
                basic_stats = {
                    "total_activities": len(activities_data),
                    "unique_contacts": len(
                        set(
                            activity.get("contact_name")
                            for activity in activities_data
                            if activity.get("contact_name")
                        )
                    ),
                    "unique_organizations": len(
                        set(
                            activity.get("contact_account_name")
                            for activity in activities_data
                            if activity.get("contact_account_name")
                        )
                    ),
                    "date_range": f"{start_date.isoformat()} to {end_date.isoformat()}",
                }

                # Structure the results (simplified)
                sql_results = {
                    "activities": activities_data,
                    "basic_stats": basic_stats,
                    "query_params": {
                        "user_id": user_id,
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                        "total_activities": len(activities_data),
                    },
                }

                # Store results in task context
                task_context.update_node(node_name=self.node_name, result=sql_results)
                task_context.metadata["sql_data_retrieved"] = True
                task_context.metadata["activity_count"] = len(activities_data)

                self.logger.info(
                    f"Successfully retrieved {len(activities_data)} individual activities with complete contact context"
                )

                return task_context

            finally:
                db_session.close()

        except Exception as e:
            self.logger.error(f"Error retrieving SQL data: {str(e)}")
            task_context.update_node(
                node_name=self.node_name, error=str(e), result=None
            )
            task_context.metadata["sql_data_retrieved"] = False
            task_context.metadata["error"] = str(e)
            return task_context

    def _get_date_range(self, event) -> tuple[date, date]:
        """
        Calculate the date range for the query.

        Args:
            event: The event containing date parameters

        Returns:
            Tuple of (start_date, end_date)
        """
        if event.start_date and event.end_date:
            return event.start_date, event.end_date

        # Default to past 30 days
        end_date = date.today()
        start_date = end_date - timedelta(days=30)

        return start_date, end_date

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
        result = {}
        for i, column in enumerate(columns):
            value = row[i]

            # Handle special types
            if isinstance(value, (datetime, date)):
                result[column] = value.isoformat()
            elif value is None:
                result[column] = None
            else:
                result[column] = value

        return result
