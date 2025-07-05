from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session

from app.database.data_models.salesforce_data import (
    SalesforceContact,
    SalesforceActivity,
)
from app.services.salesforce_files.salesforce_service import SalesforceService


class SalesforceSyncService:
    """Service for synchronizing Salesforce data with local database."""

    def __init__(self, db_session: Session, salesforce_service: SalesforceService):
        self.db = db_session
        self.sf = salesforce_service

    def sync_contacts(
        self, modified_since: Optional[datetime] = None
    ) -> List[SalesforceContact]:
        """Sync contacts modified since the given datetime."""
        # Build SOQL query
        where_clause = ""
        if modified_since:
            where_clause = f"WHERE LastModifiedDate >= {modified_since.isoformat()}Z"

        query = f"""
            SELECT Id, FirstName, LastName, Email, Phone, Title, Account.Name,
                   LastModifiedDate, CreatedDate
            FROM Contact
            {where_clause}
        """

        # Get contacts from Salesforce
        contacts = self.sf.query(query)

        # Update local database
        for contact_data in contacts:
            contact = self._upsert_contact(contact_data)

        return contacts

    def sync_activities(
        self, modified_since: Optional[datetime] = None
    ) -> List[SalesforceActivity]:
        """Sync activities (Tasks and Events) modified since the given datetime."""
        # Build SOQL query for Tasks
        where_clause = ""
        if modified_since:
            where_clause = f"WHERE LastModifiedDate >= {modified_since.isoformat()}Z"

        task_query = f"""
            SELECT Id, WhoId, Subject, Description, Status, Priority,
                   ActivityDate, LastModifiedDate, CreatedDate
            FROM Task
            {where_clause}
        """

        # Get tasks from Salesforce
        tasks = self.sf.query(task_query)

        # Update local database
        activities = []
        for task_data in tasks:
            activity = self._upsert_activity(task_data, "Task")
            activities.append(activity)

        return activities

    def _upsert_contact(self, contact_data: dict) -> SalesforceContact:
        """Create or update a contact in the local database."""
        # Check if contact exists
        contact = (
            self.db.query(SalesforceContact)
            .filter_by(salesforce_id=contact_data["Id"])
            .first()
        )

        if not contact:
            contact = SalesforceContact(salesforce_id=contact_data["Id"])

        # Update contact fields
        contact.first_name = contact_data.get("FirstName")
        contact.last_name = contact_data.get("LastName")
        contact.email = contact_data.get("Email")
        contact.phone = contact_data.get("Phone")
        contact.title = contact_data.get("Title")
        contact.company = contact_data.get("Account", {}).get("Name")
        contact.last_modified_date = datetime.fromisoformat(
            contact_data["LastModifiedDate"].rstrip("Z")
        )
        contact.created_date = datetime.fromisoformat(
            contact_data["CreatedDate"].rstrip("Z")
        )

        # Save to database
        if not contact.id:
            self.db.add(contact)
        self.db.commit()

        return contact

    def _upsert_activity(
        self, activity_data: dict, activity_type: str
    ) -> SalesforceActivity:
        """Create or update an activity in the local database."""
        # Check if activity exists
        activity = (
            self.db.query(SalesforceActivity)
            .filter_by(salesforce_id=activity_data["Id"])
            .first()
        )

        if not activity:
            activity = SalesforceActivity(salesforce_id=activity_data["Id"])

        # Get associated contact
        if activity_data.get("WhoId"):
            contact = (
                self.db.query(SalesforceContact)
                .filter_by(salesforce_id=activity_data["WhoId"])
                .first()
            )
            if contact:
                activity.contact_id = contact.id

        # Update activity fields
        activity.type = activity_type
        activity.subject = activity_data.get("Subject")
        activity.description = activity_data.get("Description")
        activity.status = activity_data.get("Status")
        activity.priority = activity_data.get("Priority")
        if activity_data.get("ActivityDate"):
            activity.activity_date = datetime.fromisoformat(
                activity_data["ActivityDate"]
            )
        activity.last_modified_date = datetime.fromisoformat(
            activity_data["LastModifiedDate"].rstrip("Z")
        )
        activity.created_date = datetime.fromisoformat(
            activity_data["CreatedDate"].rstrip("Z")
        )

        # Store additional data
        activity.additional_data = activity_data

        # Save to database
        if not activity.id:
            self.db.add(activity)
        self.db.commit()

        return activity
