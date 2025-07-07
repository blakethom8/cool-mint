from datetime import datetime
from typing import Dict, List, Optional
import logging
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert

from app.database.data_models.salesforce_data import SfUser
from app.services.salesforce_files.user_sync.rest_user_service import RestUserService

logger = logging.getLogger(__name__)


class UserSyncService:
    """Service for syncing Salesforce users with local database."""

    def __init__(self, db_session: Session, rest_service: RestUserService):
        """Initialize the user sync service.

        Args:
            db_session: SQLAlchemy database session
            rest_service: REST service for Salesforce user operations
        """
        self.db_session = db_session
        self.rest_service = rest_service

    def _transform_user_data(self, sf_user: Dict) -> Dict:
        """Transform Salesforce user data to match our database schema.

        Args:
            sf_user: Raw Salesforce user data

        Returns:
            Transformed user data matching our schema
        """
        # Create address JSON object if any address fields exist
        address = {}
        for field in [
            "Street",
            "City",
            "State",
            "PostalCode",
            "Country",
            "Latitude",
            "Longitude",
        ]:
            if sf_user.get(field):
                address[field.lower()] = sf_user[field]

        return {
            "salesforce_id": sf_user["Id"],
            "username": sf_user["Username"],
            "first_name": sf_user.get("FirstName"),
            "last_name": sf_user.get("LastName"),
            "middle_name": sf_user.get("MiddleName"),
            "suffix": sf_user.get("Suffix"),
            "name": sf_user.get("Name"),
            "email": sf_user.get("Email"),
            "is_profile_photo_active": sf_user.get("IsProfilePhotoActive", False),
            "address": address if address else None,
            "external_id": sf_user.get("External_ID__c"),
            "sf_created_date": sf_user["CreatedDate"],
            "sf_last_modified_date": sf_user["LastModifiedDate"],
            "sf_system_modstamp": sf_user["SystemModstamp"],
        }

    def _upsert_users(self, users_data: List[Dict]) -> Dict[str, int]:
        """Upsert users into the database.

        Args:
            users_data: List of transformed user data

        Returns:
            Dictionary with sync statistics
        """
        stats = {"new_records": 0, "updated_records": 0, "errors": 0}

        try:
            if not users_data:
                return stats

            # Prepare the upsert statement
            stmt = insert(SfUser).values(users_data)
            stmt = stmt.on_conflict_do_update(
                constraint="sf_users_salesforce_id_key",
                set_={
                    "username": stmt.excluded.username,
                    "first_name": stmt.excluded.first_name,
                    "last_name": stmt.excluded.last_name,
                    "middle_name": stmt.excluded.middle_name,
                    "suffix": stmt.excluded.suffix,
                    "name": stmt.excluded.name,
                    "email": stmt.excluded.email,
                    "is_profile_photo_active": stmt.excluded.is_profile_photo_active,
                    "address": stmt.excluded.address,
                    "external_id": stmt.excluded.external_id,
                    "sf_last_modified_date": stmt.excluded.sf_last_modified_date,
                    "sf_system_modstamp": stmt.excluded.sf_system_modstamp,
                },
            )

            # Execute the upsert
            result = self.db_session.execute(stmt)
            self.db_session.commit()

            # Update stats based on the result
            stats["new_records"] = result.rowcount
            stats["updated_records"] = len(users_data) - result.rowcount

        except Exception as e:
            logger.error(f"Error upserting users: {str(e)}", exc_info=True)
            stats["errors"] += 1
            self.db_session.rollback()

        return stats

    def sync_users(
        self, modified_since: Optional[datetime] = None, limit: Optional[int] = None
    ) -> Dict[str, int]:
        """Sync users from Salesforce to local database.

        Args:
            modified_since: Only sync users modified after this datetime
            limit: Optional limit on number of records to sync

        Returns:
            Dictionary with sync statistics
        """
        stats = {
            "total_retrieved": 0,
            "new_records": 0,
            "updated_records": 0,
            "errors": 0,
        }

        try:
            # Fetch users from Salesforce
            users = self.rest_service.get_users(modified_since)

            if limit:
                users = users[:limit]

            stats["total_retrieved"] = len(users)

            if not users:
                logger.info("No users found to sync")
                return stats

            # Transform and upsert users in batches
            batch_size = 200
            for i in range(0, len(users), batch_size):
                batch = users[i : i + batch_size]
                transformed_batch = [self._transform_user_data(user) for user in batch]

                batch_stats = self._upsert_users(transformed_batch)

                # Update overall stats
                stats["new_records"] += batch_stats["new_records"]
                stats["updated_records"] += batch_stats["updated_records"]
                stats["errors"] += batch_stats["errors"]

                logger.info(
                    f"Processed batch {i // batch_size + 1} of {(len(users) + batch_size - 1) // batch_size}"
                )

        except Exception as e:
            logger.error(f"Error during user sync: {str(e)}", exc_info=True)
            stats["errors"] += 1

        return stats
