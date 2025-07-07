from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
import logging

from app.database.data_models.salesforce_data import SfActivity, SfContact
from app.services.salesforce_files.activity_sync.rest_activity_service import (
    RestActivityService,
)

logger = logging.getLogger(__name__)


class ActivitySyncService:
    """Service for synchronizing Salesforce activities (Tasks and Events) with local database."""

    def __init__(self, db_session: Session, salesforce_service: RestActivityService):
        self.db = db_session
        self.sf = salesforce_service

    def sync_activities(
        self, modified_since: Optional[datetime] = None, limit: Optional[int] = None
    ) -> Dict[str, int]:
        """
        Sync both Tasks and Events from Salesforce to local database.

        Args:
            modified_since: Optional datetime to filter activities modified since
            limit: Optional limit on number of activities to sync

        Returns:
            Dictionary with sync statistics
        """
        stats = {
            "total_retrieved": 0,
            "tasks_retrieved": 0,
            "events_retrieved": 0,
            "new_records": 0,
            "updated_records": 0,
            "errors": 0,
        }

        logger.info(
            f"Starting activity sync from {modified_since if modified_since else 'all time'}"
        )

        try:
            # Sync Tasks
            logger.info("Fetching Tasks from Salesforce...")
            tasks_data = self.sf.get_tasks(modified_since)
            stats["tasks_retrieved"] = len(tasks_data)
            logger.info(f"Retrieved {stats['tasks_retrieved']} tasks")

            if limit:
                tasks_data = tasks_data[:limit]

            logger.info("Processing Tasks...")
            for i, task_data in enumerate(tasks_data, 1):
                try:
                    activity = self._upsert_activity(task_data, "Task")
                    if activity.id:  # Existing record
                        stats["updated_records"] += 1
                    else:
                        stats["new_records"] += 1

                    if i % 100 == 0:  # Log progress every 100 records
                        logger.info(f"Processed {i}/{len(tasks_data)} tasks")

                except Exception as e:
                    logger.error(
                        f"Error syncing task {task_data.get('Id', 'Unknown')}: {str(e)}"
                    )
                    stats["errors"] += 1

            # Sync Events
            logger.info("Fetching Events from Salesforce...")
            events_data = self.sf.get_events(modified_since)
            stats["events_retrieved"] = len(events_data)
            logger.info(f"Retrieved {stats['events_retrieved']} events")

            if limit:
                events_data = events_data[:limit]

            logger.info("Processing Events...")
            for i, event_data in enumerate(events_data, 1):
                try:
                    activity = self._upsert_activity(event_data, "Event")
                    if activity.id:  # Existing record
                        stats["updated_records"] += 1
                    else:
                        stats["new_records"] += 1

                    if i % 100 == 0:  # Log progress every 100 records
                        logger.info(f"Processed {i}/{len(events_data)} events")

                except Exception as e:
                    logger.error(
                        f"Error syncing event {event_data.get('Id', 'Unknown')}: {str(e)}"
                    )
                    stats["errors"] += 1

            stats["total_retrieved"] = (
                stats["tasks_retrieved"] + stats["events_retrieved"]
            )

            logger.info("Activity sync completed!")
            logger.info(f"Total activities retrieved: {stats['total_retrieved']}")
            logger.info(f"Tasks retrieved: {stats['tasks_retrieved']}")
            logger.info(f"Events retrieved: {stats['events_retrieved']}")
            logger.info(f"New records: {stats['new_records']}")
            logger.info(f"Updated records: {stats['updated_records']}")
            logger.info(f"Errors: {stats['errors']}")

            return stats

        except Exception as e:
            logger.error(f"Error during activity sync: {str(e)}")
            stats["errors"] += 1
            return stats

    def _upsert_activity(
        self, activity_data: Dict[str, Any], activity_type: str
    ) -> SfActivity:
        """Create or update an activity in the local database."""

        # Check if activity exists
        activity = (
            self.db.query(SfActivity)
            .filter_by(salesforce_id=activity_data["Id"])
            .first()
        )

        is_new = False
        if not activity:
            activity = SfActivity(salesforce_id=activity_data["Id"])
            is_new = True

        # Set basic fields
        activity.type = activity_type
        activity.subject = activity_data.get("Subject")
        activity.description = activity_data.get("Description")

        # Map standard fields
        activity.who_count = activity_data.get("WhoCount")
        activity.what_count = activity_data.get("WhatCount")
        activity.activity_date = self._parse_date(activity_data.get("ActivityDate"))
        activity.status = activity_data.get("Status", "Not Started")  # Default required
        activity.priority = activity_data.get("Priority", "Normal")  # Default required
        activity.is_high_priority = activity_data.get("IsHighPriority", False)
        activity.is_deleted = activity_data.get("IsDeleted", False)
        activity.is_closed = activity_data.get("IsClosed", False)
        activity.is_archived = activity_data.get("IsArchived", False)
        activity.task_subtype = activity_data.get("TaskSubtype")
        activity.completed_datetime = self._parse_datetime(
            activity_data.get("CompletedDateTime")
        )

        # Map custom fields
        activity.mno_subtype = activity_data.get("MNO_Subtype_c__c")
        activity.mno_primary_attendees_id = activity_data.get(
            "MNO_Primary_Attendees_ID__c"
        )
        activity.mno_type = activity_data.get("MNO_Type__c")
        activity.mn_tags = activity_data.get("MN_Tags__c")
        activity.mno_setting = activity_data.get("MNO_Setting__c")
        activity.attendees_concatenation = activity_data.get(
            "Attendees_Concatenation__c"
        )
        activity.comments_short = activity_data.get("Comments_Short__c")

        # Map relationship fields
        activity.who_id = activity_data.get("WhoId")
        activity.what_id = activity_data.get("WhatId")
        activity.owner_id = activity_data.get("OwnerId")
        activity.account_id = activity_data.get("AccountId")
        activity.created_by_id = activity_data.get("CreatedById")
        activity.last_modified_by_id = activity_data.get("LastModifiedById")

        # Map system fields
        activity.sf_created_date = self._parse_datetime(
            activity_data.get("CreatedDate")
        )
        activity.sf_last_modified_date = self._parse_datetime(
            activity_data.get("LastModifiedDate")
        )
        activity.sf_system_modstamp = self._parse_datetime(
            activity_data.get("SystemModstamp")
        )

        # Map Event-specific fields
        if activity_type == "Event":
            activity.start_datetime = self._parse_datetime(
                activity_data.get("StartDateTime")
            )
            activity.end_datetime = self._parse_datetime(
                activity_data.get("EndDateTime")
            )
            activity.duration_minutes = activity_data.get("DurationInMinutes")
            activity.location = activity_data.get("Location")
            activity.show_as = activity_data.get("ShowAs")
            activity.is_all_day_event = activity_data.get("IsAllDayEvent")
            activity.is_private = activity_data.get("IsPrivate")

        # Map related object fields
        if activity_data.get("WhoId"):
            related_contact = (
                self.db.query(SfContact)
                .filter_by(salesforce_id=activity_data["WhoId"])
                .first()
            )
            if related_contact:
                activity.contact_id = related_contact.id

        # Store additional metadata
        activity.additional_data = {
            "Account": {
                "Name": activity_data.get("Account", {}).get("Name")
                if activity_data.get("Account")
                else None,
            },
            "Who": {
                "Name": activity_data.get("Who", {}).get("Name")
                if activity_data.get("Who")
                else None,
                "Type": activity_data.get("Who", {}).get("Type")
                if activity_data.get("Who")
                else None,
            },
            "What": {
                "Name": activity_data.get("What", {}).get("Name")
                if activity_data.get("What")
                else None,
                "Type": activity_data.get("What", {}).get("Type")
                if activity_data.get("What")
                else None,
            },
        }

        # Save to database
        if is_new:
            self.db.add(activity)

        self.db.commit()
        return activity

    def _parse_datetime(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse Salesforce datetime string to Python datetime."""
        if not date_str:
            return None
        try:
            # Remove 'Z' suffix and parse
            return datetime.fromisoformat(date_str.rstrip("Z"))
        except:
            return None

    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse Salesforce date string to Python date."""
        if not date_str:
            return None
        try:
            # Remove 'Z' suffix and parse
            return datetime.fromisoformat(date_str.rstrip("Z")).date()
        except:
            return None
