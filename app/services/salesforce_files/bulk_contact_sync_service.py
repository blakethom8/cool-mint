from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
import logging

from app.database.data_models.salesforce_data import SfContact
from app.services.salesforce_files.bulk_salesforce_service import BulkSalesforceService

logger = logging.getLogger(__name__)


class BulkContactSyncService:
    """Service for bulk synchronizing Salesforce Contact data with local SfContact model.

    This service is optimized for handling large volumes of data using the Salesforce Bulk API
    and efficient database operations.
    """

    def __init__(
        self, db_session: Session, bulk_salesforce_service: BulkSalesforceService
    ):
        self.db = db_session
        self.sf_bulk = bulk_salesforce_service

    def get_contact_query(self, modified_since: Optional[datetime] = None) -> str:
        """Build the SOQL query for Contact data optimized for bulk operations."""

        # Base fields to select - same as regular sync but optimized for bulk
        fields = [
            # Standard Fields - Core Identity
            "Id",
            "LastName",
            "FirstName",
            "Salutation",
            "MiddleName",
            "Suffix",
            "Name",
            # Standard Fields - Contact Information
            "Email",
            "Phone",
            "Fax",
            "MobilePhone",
            "HomePhone",
            "OtherPhone",
            "Title",
            # Standard Fields - Mailing Address
            "MailingStreet",
            "MailingCity",
            "MailingState",
            "MailingPostalCode",
            "MailingCountry",
            "MailingLatitude",
            "MailingLongitude",
            "MailingGeocodeAccuracy",
            # Standard Fields - Activity Tracking
            "LastActivityDate",
            "LastViewedDate",
            "LastReferencedDate",
            # Custom Fields - Identity & Classification
            "External_ID__c",
            "FullName__c",
            "NPI__c",
            "Specialty__c",
            "Is_Physician__c",
            "isMyContact__c",
            "Active__c",
            # Custom Fields - Provider Information
            "Days_Since_Last_Visit__c",
            "Contact_Account_Name__c",
            "Last_Visited_By_Rep__c",
            # Custom Fields - Business Entity & Location
            "Business_Entity__c",
            "Mailing_Address_Compound__c",
            "Other_Address_Compound__c",
            # Custom Fields - Minnesota Specific
            "Employment_Status_MN__c",
            "Epic_ID__c",
            "Geography__c",
            "MN_Physician__c",
            "NPI_MN__c",
            "Network__c",
            "Network_picklist__c",
            "Onboarding_Tasks__c",
            "Outreach_Focus__c",
            "Panel_Status__c",
            "Primary_Address__c",
            "Primary_Geography__c",
            "Primary_MGMA_Specialty__c",
            "Primary_Practice_Location__c",
            "MN_Primary_SoS__c",
            "Provider_Participation__c",
            "Provider_Start_Date__c",
            "Provider_Term_Date__c",
            "Provider_Type__c",
            "Secondary_Practice_Location__c",
            "Specialty_Group__c",
            "Sub_Network__c",
            "Sub_Specialty__c",
            "MN_Primary_Geography__c",
            # Custom Fields - MN Address Components
            "MN_Address__Street__s",
            "MN_Address__City__s",
            "MN_Address__PostalCode__s",
            "MN_Address__StateCode__s",
            "MN_Address__CountryCode__s",
            "MN_Address__Latitude__s",
            "MN_Address__Longitude__s",
            "MN_Address__GeocodeAccuracy__s",
            # Custom Fields - Additional MN Data
            "Last_Outreach_Activity_Date__c",
            "MN_Secondary_SoS__c",
            "MN_MGMA_Specialty__c",
            "MN_Specialty_Group__c",
            "MN_Provider_Summary__c",
            "MN_Provider_Detailed_Notes__c",
            "MN_Tasks_Count__c",
            "MN_Name_Specialty_Network__c",
            # Salesforce System Fields
            "CreatedDate",
            "LastModifiedDate",
            "SystemModstamp",
            "LastModifiedById",
        ]

        # Build WHERE clause
        where_clause = "WHERE IsDeleted = FALSE"
        if modified_since:
            where_clause += f" AND LastModifiedDate >= {modified_since.isoformat()}Z"

        query = f"""
            SELECT {", ".join(fields)}
            FROM Contact
            {where_clause}
            ORDER BY CreatedDate ASC
        """

        return query

    def bulk_sync_contacts(
        self, modified_since: Optional[datetime] = None, batch_size: int = 1000
    ) -> Dict[str, int]:
        """Bulk sync all contacts from Salesforce to local database.

        Args:
            modified_since: Only sync contacts modified since this datetime
            batch_size: Number of records to process in each database batch

        Returns:
            Dictionary with sync statistics
        """

        stats = {
            "total_retrieved": 0,
            "total_processed": 0,
            "new_records": 0,
            "updated_records": 0,
            "errors": 0,
        }

        try:
            # Get the query
            query = self.get_contact_query(modified_since)

            # Execute bulk query
            logger.info("Starting bulk contact extraction from Salesforce...")
            contacts_data = self.sf_bulk.execute_bulk_query(query, "Contact")

            if not contacts_data:
                logger.warning("No contacts retrieved from Salesforce")
                return stats

            stats["total_retrieved"] = len(contacts_data)
            logger.info(
                f"Retrieved {stats['total_retrieved']:,} contacts from Salesforce"
            )

            # Process in batches for efficient database operations
            logger.info(f"Processing contacts in batches of {batch_size}")

            for i in range(0, len(contacts_data), batch_size):
                batch = contacts_data[i : i + batch_size]
                batch_stats = self._process_contact_batch(batch)

                # Update overall stats
                stats["total_processed"] += batch_stats["processed"]
                stats["new_records"] += batch_stats["new"]
                stats["updated_records"] += batch_stats["updated"]
                stats["errors"] += batch_stats["errors"]

                logger.info(
                    f"Processed batch {i // batch_size + 1}: {batch_stats['processed']} records"
                )

            logger.info(f"Bulk sync completed: {stats}")
            return stats

        except Exception as e:
            logger.error(f"Error during bulk sync: {str(e)}")
            stats["errors"] += 1
            return stats

    def _process_contact_batch(self, batch: List[Dict[str, Any]]) -> Dict[str, int]:
        """Process a batch of contacts with efficient database operations.

        Args:
            batch: List of contact dictionaries from Salesforce

        Returns:
            Dictionary with batch processing statistics
        """

        batch_stats = {"processed": 0, "new": 0, "updated": 0, "errors": 0}

        try:
            # Prepare data for upsert
            contact_data = []
            salesforce_ids = []

            for contact_raw in batch:
                try:
                    # Convert Salesforce data to database format
                    contact_dict = self._map_contact_data(contact_raw)
                    contact_data.append(contact_dict)
                    salesforce_ids.append(contact_raw["Id"])

                except Exception as e:
                    logger.error(
                        f"Error mapping contact {contact_raw.get('Id', 'Unknown')}: {str(e)}"
                    )
                    batch_stats["errors"] += 1
                    continue

            if not contact_data:
                return batch_stats

            # Get existing contacts to determine which are new vs updated
            existing_contacts = (
                self.db.query(SfContact.salesforce_id)
                .filter(SfContact.salesforce_id.in_(salesforce_ids))
                .all()
            )
            existing_ids = {contact.salesforce_id for contact in existing_contacts}

            # Perform bulk upsert using PostgreSQL's ON CONFLICT
            stmt = insert(SfContact).values(contact_data)

            # Define what to do on conflict (existing record)
            stmt = stmt.on_conflict_do_update(
                index_elements=["salesforce_id"],
                set_={
                    # Update all fields except id, salesforce_id, and created_at
                    column.name: stmt.excluded[column.name]
                    for column in SfContact.__table__.columns
                    if column.name not in ["id", "salesforce_id", "created_at"]
                },
            )

            # Execute the upsert
            self.db.execute(stmt)
            self.db.commit()

            # Calculate statistics
            batch_stats["processed"] = len(contact_data)
            batch_stats["new"] = len(
                [d for d in contact_data if d["salesforce_id"] not in existing_ids]
            )
            batch_stats["updated"] = len(
                [d for d in contact_data if d["salesforce_id"] in existing_ids]
            )

            return batch_stats

        except Exception as e:
            logger.error(f"Error processing batch: {str(e)}")
            self.db.rollback()
            batch_stats["errors"] = len(batch)
            return batch_stats

    def _map_contact_data(self, contact_data: Dict[str, Any]) -> Dict[str, Any]:
        """Map Salesforce contact data to database format.

        Args:
            contact_data: Raw contact data from Salesforce

        Returns:
            Dictionary formatted for database insertion
        """

        mapped_data = {
            # Required fields
            "salesforce_id": contact_data["Id"],
            "last_name": contact_data.get("LastName"),
            # Standard Fields - Core Identity
            "first_name": contact_data.get("FirstName"),
            "salutation": contact_data.get("Salutation"),
            "middle_name": contact_data.get("MiddleName"),
            "suffix": contact_data.get("Suffix"),
            "name": contact_data.get("Name"),
            # Standard Fields - Contact Information
            "email": contact_data.get("Email"),
            "phone": contact_data.get("Phone"),
            "fax": contact_data.get("Fax"),
            "mobile_phone": contact_data.get("MobilePhone"),
            "home_phone": contact_data.get("HomePhone"),
            "other_phone": contact_data.get("OtherPhone"),
            "title": contact_data.get("Title"),
            # Standard Fields - Mailing Address
            "mailing_street": contact_data.get("MailingStreet"),
            "mailing_city": contact_data.get("MailingCity"),
            "mailing_state": contact_data.get("MailingState"),
            "mailing_postal_code": contact_data.get("MailingPostalCode"),
            "mailing_country": contact_data.get("MailingCountry"),
            "mailing_latitude": self._parse_float(contact_data.get("MailingLatitude")),
            "mailing_longitude": self._parse_float(
                contact_data.get("MailingLongitude")
            ),
            "mailing_geocode_accuracy": contact_data.get("MailingGeocodeAccuracy"),
            # Standard Fields - Activity Tracking
            "last_activity_date": self._parse_date(
                contact_data.get("LastActivityDate")
            ),
            "last_viewed_date": self._parse_datetime(
                contact_data.get("LastViewedDate")
            ),
            "last_referenced_date": self._parse_datetime(
                contact_data.get("LastReferencedDate")
            ),
            # Custom Fields - Identity & Classification
            "external_id": contact_data.get("External_ID__c"),
            "full_name": contact_data.get("FullName__c"),
            "npi": contact_data.get("NPI__c"),
            "specialty": contact_data.get("Specialty__c"),
            "is_physician": self._parse_boolean(contact_data.get("Is_Physician__c")),
            "is_my_contact": self._parse_boolean(contact_data.get("isMyContact__c")),
            "active": self._parse_boolean(contact_data.get("Active__c"), default=True),
            # Custom Fields - Provider Information
            "days_since_last_visit": self._parse_float(
                contact_data.get("Days_Since_Last_Visit__c")
            ),
            "contact_account_name": contact_data.get("Contact_Account_Name__c"),
            "last_visited_by_rep_id": contact_data.get("Last_Visited_By_Rep__c"),
            # Custom Fields - Business Entity & Location
            "business_entity_id": contact_data.get("Business_Entity__c"),
            "mailing_address_compound": contact_data.get("Mailing_Address_Compound__c"),
            "other_address_compound": contact_data.get("Other_Address_Compound__c"),
            # Custom Fields - Minnesota Specific
            "employment_status_mn": contact_data.get("Employment_Status_MN__c"),
            "epic_id": contact_data.get("Epic_ID__c"),
            "geography": contact_data.get("Geography__c"),
            "mn_physician": self._parse_boolean(contact_data.get("MN_Physician__c")),
            "npi_mn": contact_data.get("NPI_MN__c"),
            "network_id": contact_data.get("Network__c"),
            "network_picklist": contact_data.get("Network_picklist__c"),
            "onboarding_tasks": self._parse_boolean(
                contact_data.get("Onboarding_Tasks__c")
            ),
            "outreach_focus": self._parse_boolean(
                contact_data.get("Outreach_Focus__c")
            ),
            "panel_status": contact_data.get("Panel_Status__c"),
            "primary_address": contact_data.get("Primary_Address__c"),
            "primary_geography": contact_data.get("Primary_Geography__c"),
            "primary_mgma_specialty": contact_data.get("Primary_MGMA_Specialty__c"),
            "primary_practice_location_id": contact_data.get(
                "Primary_Practice_Location__c"
            ),
            "mn_primary_sos_id": contact_data.get("MN_Primary_SoS__c"),
            "provider_participation": contact_data.get("Provider_Participation__c"),
            "provider_start_date": self._parse_date(
                contact_data.get("Provider_Start_Date__c")
            ),
            "provider_term_date": self._parse_date(
                contact_data.get("Provider_Term_Date__c")
            ),
            "provider_type": contact_data.get("Provider_Type__c"),
            "secondary_practice_location_id": contact_data.get(
                "Secondary_Practice_Location__c"
            ),
            "specialty_group": contact_data.get("Specialty_Group__c"),
            "sub_network": contact_data.get("Sub_Network__c"),
            "sub_specialty": contact_data.get("Sub_Specialty__c"),
            "mn_primary_geography": contact_data.get("MN_Primary_Geography__c"),
            # Custom Fields - MN Address Components
            "mn_address_street": contact_data.get("MN_Address__Street__s"),
            "mn_address_city": contact_data.get("MN_Address__City__s"),
            "mn_address_postal_code": contact_data.get("MN_Address__PostalCode__s"),
            "mn_address_state_code": contact_data.get("MN_Address__StateCode__s"),
            "mn_address_country_code": contact_data.get("MN_Address__CountryCode__s"),
            "mn_address_latitude": self._parse_float(
                contact_data.get("MN_Address__Latitude__s")
            ),
            "mn_address_longitude": self._parse_float(
                contact_data.get("MN_Address__Longitude__s")
            ),
            "mn_address_geocode_accuracy": contact_data.get(
                "MN_Address__GeocodeAccuracy__s"
            ),
            # Custom Fields - Additional MN Data
            "last_outreach_activity_date": self._parse_date(
                contact_data.get("Last_Outreach_Activity_Date__c")
            ),
            "mn_secondary_sos_id": contact_data.get("MN_Secondary_SoS__c"),
            "mn_mgma_specialty": contact_data.get("MN_MGMA_Specialty__c"),
            "mn_specialty_group": contact_data.get("MN_Specialty_Group__c"),
            "mn_provider_summary": contact_data.get("MN_Provider_Summary__c"),
            "mn_provider_detailed_notes": contact_data.get(
                "MN_Provider_Detailed_Notes__c"
            ),
            "mn_tasks_count": self._parse_float(contact_data.get("MN_Tasks_Count__c")),
            "mn_name_specialty_network": contact_data.get(
                "MN_Name_Specialty_Network__c"
            ),
            # Salesforce System Fields
            "sf_created_date": self._parse_datetime(contact_data.get("CreatedDate")),
            "sf_last_modified_date": self._parse_datetime(
                contact_data.get("LastModifiedDate")
            ),
            "sf_system_modstamp": self._parse_datetime(
                contact_data.get("SystemModstamp")
            ),
            "sf_last_modified_by_id": contact_data.get("LastModifiedById"),
            # Store raw data for reference
            "additional_data": contact_data,
            # Local metadata
            "last_synced_at": datetime.now(),
            "created_at": datetime.now(),
        }

        return mapped_data

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
            return datetime.fromisoformat(date_str).date()
        except:
            return None

    def _parse_boolean(self, value: Optional[str], default: bool = False) -> bool:
        """Parse string boolean value."""
        if value is None:
            return default
        if isinstance(value, bool):
            return value
        return str(value).lower() in ("true", "1", "yes", "on")

    def _parse_float(self, value: Optional[str]) -> Optional[float]:
        """Parse string float value."""
        if not value:
            return None
        try:
            return float(value)
        except:
            return None
