from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.database.data_models.salesforce_data import SfContact
from app.services.salesforce_files.salesforce_service import ReadOnlySalesforceService


class SfContactSyncService:
    """Service for synchronizing Salesforce Contact data with local SfContact model."""

    def __init__(
        self, db_session: Session, salesforce_service: ReadOnlySalesforceService
    ):
        self.db = db_session
        self.sf = salesforce_service

    def get_contact_query(self, modified_since: Optional[datetime] = None) -> str:
        """Build the SOQL query for Contact data."""

        # Base fields to select
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
        where_clause = ""
        if modified_since:
            where_clause = f"WHERE LastModifiedDate >= {modified_since.isoformat()}Z"

        query = f"""
            SELECT {", ".join(fields)}
            FROM Contact
            {where_clause}
            ORDER BY LastModifiedDate DESC
        """

        return query

    def sync_contacts(
        self, modified_since: Optional[datetime] = None, limit: Optional[int] = None
    ) -> List[SfContact]:
        """Sync contacts from Salesforce to local database."""

        # Get the query
        query = self.get_contact_query(modified_since)

        # Add limit if specified
        if limit:
            query += f" LIMIT {limit}"

        print(f"Executing query: {query[:100]}...")  # Show first 100 chars

        # Execute query
        contacts_data = self.sf.query(query)

        print(f"Retrieved {len(contacts_data)} contacts from Salesforce")

        # Process each contact
        synced_contacts = []
        for contact_data in contacts_data:
            try:
                contact = self._upsert_contact(contact_data)
                synced_contacts.append(contact)
            except Exception as e:
                print(
                    f"Error syncing contact {contact_data.get('Id', 'Unknown')}: {str(e)}"
                )

        print(f"Successfully synced {len(synced_contacts)} contacts")
        return synced_contacts

    def _upsert_contact(self, contact_data: Dict[str, Any]) -> SfContact:
        """Create or update a contact in the local database."""

        # Check if contact exists
        contact = (
            self.db.query(SfContact).filter_by(salesforce_id=contact_data["Id"]).first()
        )

        is_new = False
        if not contact:
            contact = SfContact(salesforce_id=contact_data["Id"])
            is_new = True

        # Map Standard Fields - Core Identity
        contact.last_name = contact_data.get("LastName")
        contact.first_name = contact_data.get("FirstName")
        contact.salutation = contact_data.get("Salutation")
        contact.middle_name = contact_data.get("MiddleName")
        contact.suffix = contact_data.get("Suffix")
        contact.name = contact_data.get("Name")

        # Map Standard Fields - Contact Information
        contact.email = contact_data.get("Email")
        contact.phone = contact_data.get("Phone")
        contact.fax = contact_data.get("Fax")
        contact.mobile_phone = contact_data.get("MobilePhone")
        contact.home_phone = contact_data.get("HomePhone")
        contact.other_phone = contact_data.get("OtherPhone")
        contact.title = contact_data.get("Title")

        # Map Standard Fields - Mailing Address
        contact.mailing_street = contact_data.get("MailingStreet")
        contact.mailing_city = contact_data.get("MailingCity")
        contact.mailing_state = contact_data.get("MailingState")
        contact.mailing_postal_code = contact_data.get("MailingPostalCode")
        contact.mailing_country = contact_data.get("MailingCountry")
        contact.mailing_latitude = contact_data.get("MailingLatitude")
        contact.mailing_longitude = contact_data.get("MailingLongitude")
        contact.mailing_geocode_accuracy = contact_data.get("MailingGeocodeAccuracy")

        # Map Standard Fields - Activity Tracking
        contact.last_activity_date = self._parse_date(
            contact_data.get("LastActivityDate")
        )
        contact.last_viewed_date = self._parse_datetime(
            contact_data.get("LastViewedDate")
        )
        contact.last_referenced_date = self._parse_datetime(
            contact_data.get("LastReferencedDate")
        )

        # Map Custom Fields - Identity & Classification
        contact.external_id = contact_data.get("External_ID__c")
        contact.full_name = contact_data.get("FullName__c")
        contact.npi = contact_data.get("NPI__c")
        contact.specialty = contact_data.get("Specialty__c")
        contact.is_physician = contact_data.get("Is_Physician__c", False)
        contact.is_my_contact = contact_data.get("isMyContact__c", False)
        contact.active = contact_data.get("Active__c", True)

        # Map Custom Fields - Provider Information
        contact.days_since_last_visit = contact_data.get("Days_Since_Last_Visit__c")
        contact.contact_account_name = contact_data.get("Contact_Account_Name__c")
        contact.last_visited_by_rep_id = contact_data.get("Last_Visited_By_Rep__c")

        # Map Custom Fields - Business Entity & Location
        contact.business_entity_id = contact_data.get("Business_Entity__c")
        contact.mailing_address_compound = contact_data.get(
            "Mailing_Address_Compound__c"
        )
        contact.other_address_compound = contact_data.get("Other_Address_Compound__c")

        # Map Custom Fields - Minnesota Specific
        contact.employment_status_mn = contact_data.get("Employment_Status_MN__c")
        contact.epic_id = contact_data.get("Epic_ID__c")
        contact.geography = contact_data.get("Geography__c")
        contact.mn_physician = contact_data.get("MN_Physician__c", False)
        contact.npi_mn = contact_data.get("NPI_MN__c")
        contact.network_id = contact_data.get("Network__c")
        contact.network_picklist = contact_data.get("Network_picklist__c")
        contact.onboarding_tasks = contact_data.get("Onboarding_Tasks__c", False)
        contact.outreach_focus = contact_data.get("Outreach_Focus__c", False)
        contact.panel_status = contact_data.get("Panel_Status__c")
        contact.primary_address = contact_data.get("Primary_Address__c")
        contact.primary_geography = contact_data.get("Primary_Geography__c")
        contact.primary_mgma_specialty = contact_data.get("Primary_MGMA_Specialty__c")
        contact.primary_practice_location_id = contact_data.get(
            "Primary_Practice_Location__c"
        )
        contact.mn_primary_sos_id = contact_data.get("MN_Primary_SoS__c")
        contact.provider_participation = contact_data.get("Provider_Participation__c")
        contact.provider_start_date = self._parse_date(
            contact_data.get("Provider_Start_Date__c")
        )
        contact.provider_term_date = self._parse_date(
            contact_data.get("Provider_Term_Date__c")
        )
        contact.provider_type = contact_data.get("Provider_Type__c")
        contact.secondary_practice_location_id = contact_data.get(
            "Secondary_Practice_Location__c"
        )
        contact.specialty_group = contact_data.get("Specialty_Group__c")
        contact.sub_network = contact_data.get("Sub_Network__c")
        contact.sub_specialty = contact_data.get("Sub_Specialty__c")
        contact.mn_primary_geography = contact_data.get("MN_Primary_Geography__c")

        # Map Custom Fields - MN Address Components
        contact.mn_address_street = contact_data.get("MN_Address__Street__s")
        contact.mn_address_city = contact_data.get("MN_Address__City__s")
        contact.mn_address_postal_code = contact_data.get("MN_Address__PostalCode__s")
        contact.mn_address_state_code = contact_data.get("MN_Address__StateCode__s")
        contact.mn_address_country_code = contact_data.get("MN_Address__CountryCode__s")
        contact.mn_address_latitude = contact_data.get("MN_Address__Latitude__s")
        contact.mn_address_longitude = contact_data.get("MN_Address__Longitude__s")
        contact.mn_address_geocode_accuracy = contact_data.get(
            "MN_Address__GeocodeAccuracy__s"
        )

        # Map Custom Fields - Additional MN Data
        contact.last_outreach_activity_date = self._parse_date(
            contact_data.get("Last_Outreach_Activity_Date__c")
        )
        contact.mn_secondary_sos_id = contact_data.get("MN_Secondary_SoS__c")
        contact.mn_mgma_specialty = contact_data.get("MN_MGMA_Specialty__c")
        contact.mn_specialty_group = contact_data.get("MN_Specialty_Group__c")
        contact.mn_provider_summary = contact_data.get("MN_Provider_Summary__c")
        contact.mn_provider_detailed_notes = contact_data.get(
            "MN_Provider_Detailed_Notes__c"
        )
        contact.mn_tasks_count = contact_data.get("MN_Tasks_Count__c")
        contact.mn_name_specialty_network = contact_data.get(
            "MN_Name_Specialty_Network__c"
        )

        # Map Salesforce System Fields
        contact.sf_created_date = self._parse_datetime(contact_data.get("CreatedDate"))
        contact.sf_last_modified_date = self._parse_datetime(
            contact_data.get("LastModifiedDate")
        )
        contact.sf_system_modstamp = self._parse_datetime(
            contact_data.get("SystemModstamp")
        )
        contact.sf_last_modified_by_id = contact_data.get("LastModifiedById")

        # Store raw data for reference
        contact.additional_data = contact_data

        # Save to database
        if is_new:
            self.db.add(contact)

        self.db.commit()
        return contact

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
