"""
CSV Data Import Script for Market Explorer 2.0

This script imports data from the provided CSV files into the PostgreSQL database:
- Providers.csv -> claims_providers table
- SoS.csv -> sites_of_service table  
- Visits.csv -> claims_visits table

The script handles UTF-8 BOM encoding, generates UUIDs for sites of service,
and establishes proper relationships between the tables.
"""

import uuid
import pandas as pd
import logging
from pathlib import Path
from typing import Dict, List, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from database.database_utils import DatabaseUtils
from database.data_models.claims_data import ClaimsProvider, SiteOfService, ClaimsVisit

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ClaimsDataImporter:
    def __init__(self, csv_directory: str):
        self.csv_directory = Path(csv_directory)
        self.engine = create_engine(DatabaseUtils.get_connection_string())
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # Mappings to store relationships
        self.site_id_mapping: Dict[str, str] = {}  # legacy_id -> uuid
        self.provider_npi_mapping: Dict[str, str] = {}  # npi -> uuid
        
    def clean_csv_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean CSV data by handling UTF-8 BOM and other encoding issues."""
        # Remove BOM characters from column names
        df.columns = df.columns.str.replace('\ufeff', '')
        
        # Strip whitespace from string columns
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].astype(str).str.strip()
                # Replace 'nan' strings with None
                df[col] = df[col].replace('nan', None)
        
        return df
    
    def import_providers(self) -> None:
        """Import providers from Providers.csv"""
        logger.info("Starting provider import...")
        
        providers_file = self.csv_directory / "Providers.csv"
        if not providers_file.exists():
            logger.error(f"Providers.csv not found at {providers_file}")
            return
            
        # Read CSV with proper encoding handling (UTF-16)
        df = pd.read_csv(providers_file, encoding='utf-16', sep='\t')
        df = self.clean_csv_data(df)
        
        logger.info(f"Loaded {len(df)} providers from CSV")
        
        session = self.SessionLocal()
        try:
            imported_count = 0
            skipped_count = 0
            
            for _, row in df.iterrows():
                try:
                    # Check if provider already exists
                    npi = row.get('Lead_NPI')
                    if not npi or pd.isna(npi):
                        logger.warning(f"Skipping provider with missing NPI: {row.get('Lead_Name', 'Unknown')}")
                        skipped_count += 1
                        continue
                    
                    existing_provider = session.query(ClaimsProvider).filter_by(npi=str(npi)).first()
                    if existing_provider:
                        logger.debug(f"Provider with NPI {npi} already exists, skipping")
                        skipped_count += 1
                        continue
                    
                    provider_id = uuid.uuid4()
                    
                    provider = ClaimsProvider(
                        id=provider_id,
                        npi=str(npi),
                        name=row.get('Lead_Name'),
                        specialty=row.get('Lead_Specialty'),
                        geomarket=row.get('Lead_Top_Geomarket'),
                        provider_group=row.get('Lead_Provider_Group'),
                        specialty_grandparent=row.get('Lead_Specialty_Grandparent'),
                        service_line=row.get('Lead_Service_Line'),
                        top_payer=row.get('Lead_Top_Payer'),
                        top_payer_percent=self._safe_float(row.get('Lead_Top_Payer_Percent')),
                        top_referring_org=row.get('Lead_Top_Referring_Org'),
                        top_sos_name=row.get('Lead_Top_SoS'),
                        top_sos_latitude=self._safe_float(row.get('Lead_Top_Latitude')),
                        top_sos_longitude=self._safe_float(row.get('Lead_Top_Longitude')),
                        top_sos_address=row.get('Lead_Top_SoS_Address'),
                        top_sos_id=row.get('Lead_Top_SoS_ID'),
                        total_visits=self._safe_int(row.get('Lead_Total_Visits'))
                    )
                    
                    session.add(provider)
                    self.provider_npi_mapping[str(npi)] = str(provider_id)
                    imported_count += 1
                    
                    if imported_count % 100 == 0:
                        logger.info(f"Imported {imported_count} providers...")
                        session.commit()
                        
                except Exception as e:
                    logger.error(f"Error importing provider {row.get('Lead_Name', 'Unknown')}: {e}")
                    skipped_count += 1
                    continue
            
            session.commit()
            logger.info(f"Provider import complete. Imported: {imported_count}, Skipped: {skipped_count}")
            
        except Exception as e:
            logger.error(f"Error during provider import: {e}")
            session.rollback()
        finally:
            session.close()
    
    def import_sites(self) -> None:
        """Import sites of service from SoS.csv"""
        logger.info("Starting site of service import...")
        
        sos_file = self.csv_directory / "SoS.csv"
        if not sos_file.exists():
            logger.error(f"SoS.csv not found at {sos_file}")
            return
            
        df = pd.read_csv(sos_file, encoding='utf-16', sep='\t')
        df = self.clean_csv_data(df)
        
        logger.info(f"Loaded {len(df)} sites from CSV")
        
        session = self.SessionLocal()
        try:
            imported_count = 0
            skipped_count = 0
            
            for _, row in df.iterrows():
                try:
                    legacy_id = row.get('SoS_ID')
                    if not legacy_id or pd.isna(legacy_id):
                        logger.warning(f"Skipping site with missing ID: {row.get('SoS_Name', 'Unknown')}")
                        skipped_count += 1
                        continue
                    
                    # Check if site already exists
                    existing_site = session.query(SiteOfService).filter_by(legacy_id=str(legacy_id)).first()
                    if existing_site:
                        logger.debug(f"Site with legacy ID {legacy_id} already exists, skipping")
                        self.site_id_mapping[str(legacy_id)] = str(existing_site.id)
                        skipped_count += 1
                        continue
                    
                    site_id = uuid.uuid4()
                    
                    site_name = row.get('SoS_Name')
                    if not site_name or pd.isna(site_name) or str(site_name).lower() in ['none', 'null', 'nan']:
                        site_name = self._extract_name_from_legacy_id(str(legacy_id))
                    
                    site = SiteOfService(
                        id=site_id,
                        legacy_id=str(legacy_id),
                        name=site_name,
                        city=row.get('SoS_City'),
                        county=row.get('SoS_County'),
                        site_type=row.get('SoS_Type'),
                        zip_code=row.get('SoS_Zip'),
                        latitude=self._safe_float(row.get('SoS_Latitude')),
                        longitude=self._safe_float(row.get('SoS_Longitude')),
                        geomarket=row.get('SoS_Geomarket'),
                        address=self._extract_address_from_legacy_id(str(legacy_id))
                    )
                    
                    session.add(site)
                    self.site_id_mapping[str(legacy_id)] = str(site_id)
                    imported_count += 1
                    
                    if imported_count % 100 == 0:
                        logger.info(f"Imported {imported_count} sites...")
                        session.commit()
                        
                except Exception as e:
                    logger.error(f"Error importing site {row.get('SoS_Name', 'Unknown')}: {e}")
                    session.rollback()
                    skipped_count += 1
                    continue
            
            session.commit()
            logger.info(f"Site import complete. Imported: {imported_count}, Skipped: {skipped_count}")
            
        except Exception as e:
            logger.error(f"Error during site import: {e}")
            session.rollback()
        finally:
            session.close()
    
    def import_visits(self) -> None:
        """Import visit data from Visits.csv"""
        logger.info("Starting visit import...")
        
        visits_file = self.csv_directory / "Visits.csv"
        if not visits_file.exists():
            logger.error(f"Visits.csv not found at {visits_file}")
            return
            
        df = pd.read_csv(visits_file, encoding='utf-16', sep='\t')
        df = self.clean_csv_data(df)
        
        logger.info(f"Loaded {len(df)} visit records from CSV")
        
        session = self.SessionLocal()
        try:
            imported_count = 0
            skipped_count = 0
            
            for _, row in df.iterrows():
                try:
                    npi = str(row.get('Lead_NPI', ''))
                    sos_id = str(row.get('SoS_ID', ''))
                    
                    if not npi or not sos_id or pd.isna(npi) or pd.isna(sos_id):
                        logger.warning(f"Skipping visit record with missing NPI or SoS_ID")
                        skipped_count += 1
                        continue
                    
                    # Get provider and site UUIDs
                    provider_uuid = self.provider_npi_mapping.get(npi)
                    site_uuid = self.site_id_mapping.get(sos_id)
                    
                    if not provider_uuid:
                        logger.warning(f"Provider with NPI {npi} not found in mapping")
                        skipped_count += 1
                        continue
                        
                    if not site_uuid:
                        logger.warning(f"Site with legacy ID {sos_id} not found in mapping")
                        skipped_count += 1
                        continue
                    
                    # Check if visit record already exists
                    existing_visit = session.query(ClaimsVisit).filter_by(
                        provider_id=provider_uuid,
                        site_id=site_uuid,
                        has_oncology=bool(row.get('visit_has_oncology', 0)),
                        has_surgery=bool(row.get('visit_has_surgery', 0)),
                        has_inpatient=bool(row.get('lead_has_inpatient', 0))
                    ).first()
                    
                    if existing_visit:
                        # Update existing visit count
                        existing_visit.visits += self._safe_int(row.get('Visits', 0))
                        imported_count += 1
                    else:
                        # Create new visit record
                        visit = ClaimsVisit(
                            id=uuid.uuid4(),
                            provider_id=provider_uuid,
                            site_id=site_uuid,
                            visits=self._safe_int(row.get('Visits', 0)),
                            has_oncology=bool(row.get('visit_has_oncology', 0)),
                            has_surgery=bool(row.get('visit_has_surgery', 0)),
                            has_inpatient=bool(row.get('lead_has_inpatient', 0))
                        )
                        
                        session.add(visit)
                        imported_count += 1
                    
                    if imported_count % 100 == 0:
                        logger.info(f"Processed {imported_count} visit records...")
                        session.commit()
                        
                except Exception as e:
                    logger.error(f"Error importing visit record: {e}")
                    skipped_count += 1
                    continue
            
            session.commit()
            logger.info(f"Visit import complete. Imported: {imported_count}, Skipped: {skipped_count}")
            
        except Exception as e:
            logger.error(f"Error during visit import: {e}")
            session.rollback()
        finally:
            session.close()
    
    def _safe_float(self, value) -> Optional[float]:
        """Safely convert value to float, return None if invalid"""
        if pd.isna(value) or value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def _safe_int(self, value) -> int:
        """Safely convert value to int, return 0 if invalid"""
        if pd.isna(value) or value is None:
            return 0
        try:
            # Handle comma-separated numbers like "1,182"
            if isinstance(value, str):
                value = value.replace(',', '')
            return int(float(value))
        except (ValueError, TypeError):
            return 0
    
    def _extract_address_from_legacy_id(self, legacy_id: str) -> Optional[str]:
        """Extract address from legacy ID format 'NAME - ADDRESS'"""
        if '-' in legacy_id:
            parts = legacy_id.split('-', 1)
            if len(parts) > 1:
                return parts[1].strip()
        return None
    
    def _extract_name_from_legacy_id(self, legacy_id: str) -> str:
        """Extract name from legacy ID format 'NAME - ADDRESS'"""
        if '-' in legacy_id:
            parts = legacy_id.split('-', 1)
            return parts[0].strip()
        return legacy_id
    
    def run_import(self) -> None:
        """Run the complete import process"""
        logger.info("Starting complete claims data import...")
        
        # Import in order: providers first, then sites, then visits
        self.import_providers()
        self.import_sites()
        self.import_visits()
        
        logger.info("Claims data import complete!")


def main():
    """Main function to run the import"""
    import sys
    import os
    
    # Add app directory to Python path
    app_dir = Path(__file__).parent.parent
    sys.path.insert(0, str(app_dir))
    
    # CSV directory path
    csv_directory = app_dir.parent / "CSV"
    
    if not csv_directory.exists():
        logger.error(f"CSV directory not found at {csv_directory}")
        return
    
    importer = ClaimsDataImporter(str(csv_directory))
    importer.run_import()


if __name__ == "__main__":
    main()