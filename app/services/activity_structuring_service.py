"""
Activity Structuring Service

This service populates the sf_activities_structured table with pre-structured
activity data optimized for LLM consumption and agent workflows.

Leverages the existing MonthlyActivitySummaryAnalyzer logic to structure data.
"""

import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional
from collections import Counter
from sqlalchemy.orm import Session
from sqlalchemy import text, and_

from database.session import SessionLocal
from database.data_models.salesforce_data import (
    SfActivity,
    SfActivityStructured,
    SfUser,
)
from workflows.salesforce_data_analyzer.analyzers import (
    MonthlyActivitySummaryAnalyzer,
)


class ActivityStructuringService:
    """
    Service for structuring activity data and populating sf_activities_structured table.

    This service:
    1. Uses MonthlyActivitySummaryAnalyzer to get structured activity data
    2. Transforms it into the sf_activities_structured format
    3. Handles incremental updates and deduplication
    4. Provides batch processing capabilities
    """

    def __init__(self, debug_mode: bool = False):
        self.debug_mode = debug_mode
        self.logger = logging.getLogger(__name__)
        self.analyzer = MonthlyActivitySummaryAnalyzer(debug_mode=debug_mode)

    def structure_activity(
        self, activity_id: str, db_session: Optional[Session] = None
    ) -> bool:
        """
        Structure a single activity and save to sf_activities_structured.

        Args:
            activity_id: UUID or Salesforce ID of the activity to structure
            db_session: Optional database session (creates new one if not provided)

        Returns:
            True if successful, False otherwise
        """
        should_close_session = False
        if db_session is None:
            db_session = SessionLocal()
            should_close_session = True

        try:
            # Get the activity
            activity = self._get_activity(activity_id, db_session)
            if not activity:
                self.logger.warning(f"Activity not found: {activity_id}")
                return False

            self.logger.info(
                f"Structuring activity: {activity.id} ({activity.salesforce_id})"
            )

            # Use analyzer to get structured data for this activity
            query_params = {
                "user_id": activity.owner_id,
                "start_date": activity.activity_date,
                "end_date": activity.activity_date,  # Single day range
            }

            # Get structured data using analyzer
            structured_data = self.analyzer.execute_and_structure(
                db_session, query_params
            )

            # Find our activity in the structured data
            activity_data = None
            for act in structured_data.get("activities", []):
                if act.get("activity_id") == str(activity.id):
                    activity_data = act
                    break

            if not activity_data:
                self.logger.warning(
                    f"Activity not found in structured data: {activity.id}"
                )
                return False

            # Get user info
            user_name = self._get_user_name(activity.owner_id, db_session)

            # Transform to sf_activities_structured format
            structured_record = self._transform_to_structured_record(
                activity, activity_data, user_name, structured_data
            )

            # Save to database
            return self._save_structured_record(structured_record, db_session)

        except Exception as e:
            self.logger.error(f"Error structuring activity {activity_id}: {str(e)}")
            return False

        finally:
            if should_close_session:
                db_session.close()

    def structure_activities_batch(
        self, user_id: str, start_date: date, end_date: date, batch_size: int = 100
    ) -> Dict[str, Any]:
        """
        Structure activities in batch for a user within a date range.

        Args:
            user_id: Salesforce user ID
            start_date: Start date for activities
            end_date: End date for activities
            batch_size: Number of activities to process at once

        Returns:
            Summary of processing results
        """
        db_session = SessionLocal()
        results = {
            "total_activities": 0,
            "successful": 0,
            "failed": 0,
            "overwritten": 0,
            "errors": [],
        }

        try:
            self.logger.info(
                f"Batch structuring activities for user {user_id} from {start_date} to {end_date}"
            )

            # Get user info once
            user_name = self._get_user_name(user_id, db_session)

            # Use analyzer to get all structured data for the period
            query_params = {
                "user_id": user_id,
                "start_date": start_date,
                "end_date": end_date,
            }

            structured_data = self.analyzer.execute_and_structure(
                db_session, query_params
            )
            activities_data = structured_data.get("activities", [])

            results["total_activities"] = len(activities_data)

            # Process in batches
            for i in range(0, len(activities_data), batch_size):
                batch = activities_data[i : i + batch_size]
                batch_results = self._process_batch(
                    batch, user_name, structured_data, db_session
                )

                results["successful"] += batch_results["successful"]
                results["failed"] += batch_results["failed"]
                results["overwritten"] += batch_results["overwritten"]
                results["errors"].extend(batch_results["errors"])

                if self.debug_mode:
                    self.logger.info(
                        f"Processed batch {i // batch_size + 1}: {batch_results}"
                    )

            db_session.commit()
            self.logger.info(f"Batch processing complete: {results}")

        except Exception as e:
            self.logger.error(f"Error in batch processing: {str(e)}")
            db_session.rollback()
            results["errors"].append(str(e))

        finally:
            db_session.close()

        return results

    def rebuild_all_activities(self, days_back: int = 365) -> Dict[str, Any]:
        """
        Rebuild all activity structures for the past N days.

        Args:
            days_back: Number of days back to process

        Returns:
            Summary of processing results
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days_back)

        db_session = SessionLocal()
        results = {
            "users_processed": 0,
            "total_activities": 0,
            "successful": 0,
            "failed": 0,
            "errors": [],
        }

        try:
            # Get all users who have activities in the date range
            user_ids = self._get_active_user_ids(start_date, end_date, db_session)
            results["users_processed"] = len(user_ids)

            self.logger.info(
                f"Rebuilding activities for {len(user_ids)} users from {start_date} to {end_date}"
            )

            for user_id in user_ids:
                try:
                    user_results = self.structure_activities_batch(
                        user_id, start_date, end_date
                    )
                    results["total_activities"] += user_results["total_activities"]
                    results["successful"] += user_results["successful"]
                    results["failed"] += user_results["failed"]
                    results["errors"].extend(user_results["errors"])

                except Exception as e:
                    error_msg = f"Error processing user {user_id}: {str(e)}"
                    self.logger.error(error_msg)
                    results["errors"].append(error_msg)
                    results["failed"] += 1

        finally:
            db_session.close()

        return results

    def _get_activity(
        self, activity_id: str, db_session: Session
    ) -> Optional[SfActivity]:
        """Get activity by ID or Salesforce ID."""
        # Try UUID first
        try:
            activity = (
                db_session.query(SfActivity)
                .filter(SfActivity.id == activity_id)
                .first()
            )
            if activity:
                return activity
        except:
            pass

        # Try Salesforce ID
        return (
            db_session.query(SfActivity)
            .filter(SfActivity.salesforce_id == activity_id)
            .first()
        )

    def _get_user_name(self, user_id: str, db_session: Session) -> str:
        """Get user name from user ID."""
        user = db_session.query(SfUser).filter(SfUser.salesforce_id == user_id).first()
        return user.name if user else "Unknown User"

    def _get_active_user_ids(
        self, start_date: date, end_date: date, db_session: Session
    ) -> List[str]:
        """Get all user IDs who have activities in the date range."""
        result = db_session.execute(
            text("""
                SELECT DISTINCT owner_id 
                FROM sf_activities 
                WHERE activity_date >= :start_date 
                  AND activity_date <= :end_date
                  AND is_deleted = false
                  AND description IS NOT NULL
                  AND description != ''
            """),
            {"start_date": start_date, "end_date": end_date},
        )
        return [row[0] for row in result.fetchall()]

    def _transform_to_structured_record(
        self,
        activity: SfActivity,
        activity_data: Dict[str, Any],
        user_name: str,
        full_structured_data: Dict[str, Any],
    ) -> SfActivityStructured:
        """Transform analyzer output to SfActivityStructured record."""

        activity_info = activity_data.get("activity_info", {})
        contacts = activity_data.get("contacts", [])

        # Extract contact arrays
        contact_names = [
            c.get("contact_name") for c in contacts if c.get("contact_name")
        ]
        contact_specialties = [
            c.get("specialty") for c in contacts if c.get("specialty")
        ]
        contact_cities = [
            c.get("mailing_city") for c in contacts if c.get("mailing_city")
        ]
        contact_accounts = [
            c.get("organization") for c in contacts if c.get("organization")
        ]
        geographies = [
            c.get("mn_primary_geography")
            for c in contacts
            if c.get("mn_primary_geography")
        ]

        # Calculate aggregations
        physician_count = sum(1 for c in contacts if c.get("is_physician"))
        has_community = any(c.get("employment_status") == "Community" for c in contacts)

        # Primary specialty (most common)
        specialty_counts = Counter(contact_specialties)
        primary_specialty = (
            specialty_counts.most_common(1)[0][0] if specialty_counts else None
        )

        # Specialty mix
        specialty_mix = "unknown"
        if len(specialty_counts) == 0:
            specialty_mix = "unknown"
        elif len(specialty_counts) == 1:
            specialty_mix = "single"
        else:
            specialty_mix = "multi"

        # Geographic aggregations
        geography_counts = Counter(geographies)
        primary_geography = (
            geography_counts.most_common(1)[0][0] if geography_counts else None
        )

        geographic_mix = "unknown"
        if len(geography_counts) == 0:
            geographic_mix = "unknown"
        elif len(geography_counts) == 1:
            geographic_mix = "single"
        else:
            geographic_mix = "multi"

        # Time-based fields
        activity_date = activity.activity_date
        activity_month = activity_date.strftime("%Y-%m") if activity_date else None
        activity_quarter = (
            f"{activity_date.year}-Q{(activity_date.month - 1) // 3 + 1}"
            if activity_date
            else None
        )
        activity_year = activity_date.year if activity_date else None

        # Create structured record
        return SfActivityStructured(
            source_activity_id=activity.id,
            salesforce_activity_id=activity.salesforce_id,
            # Core activity fields
            activity_date=activity.activity_date,
            subject=activity.subject,
            description=activity.description,
            status=activity.status,
            priority=activity.priority,
            # Activity classification
            mno_type=activity.mno_type,
            mno_subtype=activity.mno_subtype,
            mno_setting=getattr(activity, "mno_setting", None),
            type=activity.type,
            # User information
            owner_id=activity.owner_id,
            user_name=user_name,
            # Contact metrics
            contact_count=len(contacts),
            physician_count=physician_count,
            # Contact arrays
            contact_names=contact_names,
            contact_specialties=contact_specialties,
            contact_account_names=contact_accounts,
            contact_mailing_cities=contact_cities,
            mn_primary_geographies=geographies,
            # Boolean flags
            activity_has_community=has_community,
            activity_has_physicians=physician_count > 0,
            activity_has_high_priority=(activity.priority == "High"),
            activity_is_completed=(activity.status == "Completed"),
            # Aggregations
            primary_specialty=primary_specialty,
            specialty_mix=specialty_mix,
            primary_geography=primary_geography,
            geographic_mix=geographic_mix,
            # Time-based
            activity_month=activity_month,
            activity_quarter=activity_quarter,
            activity_year=activity_year,
            # LLM Context (the complete activity data ready for LLM)
            llm_context_json=activity_data,
            # Metadata
            data_version="1.0",
            structured_at=datetime.utcnow(),
            source_last_modified=activity.sf_last_modified_date,
            is_current=True,
        )

    def _process_batch(
        self,
        batch: List[Dict[str, Any]],
        user_name: str,
        full_structured_data: Dict[str, Any],
        db_session: Session,
    ) -> Dict[str, Any]:
        """Process a batch of activities."""
        results = {"successful": 0, "failed": 0, "overwritten": 0, "errors": []}

        # Step 1: Collect all activity IDs and delete existing records first
        activity_ids = [
            data.get("activity_id") for data in batch if data.get("activity_id")
        ]

        if activity_ids:
            # Delete all existing records for these activities
            deleted_count = (
                db_session.query(SfActivityStructured)
                .filter(SfActivityStructured.source_activity_id.in_(activity_ids))
                .delete(synchronize_session=False)
            )

            if deleted_count > 0:
                results["overwritten"] = deleted_count
                # Commit the deletes first to avoid unique constraint violations
                db_session.commit()

        # Step 2: Process each activity and insert new records
        for activity_data in batch:
            try:
                activity_id = activity_data.get("activity_id")
                if not activity_id:
                    continue

                # Get the source activity
                activity = (
                    db_session.query(SfActivity)
                    .filter(SfActivity.id == activity_id)
                    .first()
                )
                if not activity:
                    results["failed"] += 1
                    continue

                # Transform and save
                structured_record = self._transform_to_structured_record(
                    activity, activity_data, user_name, full_structured_data
                )

                db_session.add(structured_record)
                results["successful"] += 1

            except Exception as e:
                error_msg = f"Error processing activity {activity_data.get('activity_id', 'unknown')}: {str(e)}"
                results["errors"].append(error_msg)
                results["failed"] += 1

        return results

    def _save_structured_record(
        self, record: SfActivityStructured, db_session: Session
    ) -> bool:
        """Save structured record to database."""
        try:
            # Mark any existing records as not current
            db_session.query(SfActivityStructured).filter(
                SfActivityStructured.source_activity_id == record.source_activity_id
            ).update({"is_current": False})

            # Add new record
            db_session.add(record)
            db_session.commit()

            self.logger.info(
                f"Saved structured record for activity: {record.source_activity_id}"
            )
            return True

        except Exception as e:
            self.logger.error(f"Error saving structured record: {str(e)}")
            db_session.rollback()
            return False
