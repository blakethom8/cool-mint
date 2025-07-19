"""
Import visits data only from Visits.csv

This script imports only the visits data, assuming providers and sites are already imported.
"""

import uuid
import pandas as pd
import logging
from pathlib import Path
from typing import Dict
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.database_utils import DatabaseUtils
from database.data_models.claims_data import ClaimsProvider, SiteOfService, ClaimsVisit

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def import_visits_only():
    """Import visits data from CSV"""
    
    # Setup database connection
    engine = create_engine(DatabaseUtils.get_connection_string())
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    try:
        # Build mapping from NPIs to provider UUIDs
        logger.info("Building provider NPI mapping...")
        providers = session.query(ClaimsProvider.npi, ClaimsProvider.id).all()
        npi_to_uuid = {npi: str(provider_id) for npi, provider_id in providers}
        logger.info(f"Found {len(npi_to_uuid)} providers")
        
        # Build mapping from legacy IDs to site UUIDs
        logger.info("Building site legacy ID mapping...")
        sites = session.query(SiteOfService.legacy_id, SiteOfService.id).all()
        legacy_to_uuid = {legacy_id: str(site_id) for legacy_id, site_id in sites}
        logger.info(f"Found {len(legacy_to_uuid)} sites")
        
        # Load visits CSV
        csv_file = Path("/Users/blakethomson/Documents/Repo/cool-mint/CSV/Visits.csv")
        logger.info(f"Loading visits from {csv_file}")
        
        df = pd.read_csv(csv_file, encoding='utf-16', sep='\t')
        
        # Clean column names
        df.columns = df.columns.str.replace('\ufeff', '')
        
        # Strip whitespace and handle NaN
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].astype(str).str.strip()
                df[col] = df[col].replace('nan', None)
        
        logger.info(f"Loaded {len(df)} visit records from CSV")
        
        imported_count = 0
        skipped_count = 0
        
        for _, row in df.iterrows():
            try:
                npi = str(row.get('Lead_NPI', ''))
                sos_id = str(row.get('SoS_ID', ''))
                
                if not npi or not sos_id or pd.isna(npi) or pd.isna(sos_id):
                    skipped_count += 1
                    continue
                
                # Get UUIDs
                provider_uuid = npi_to_uuid.get(npi)
                site_uuid = legacy_to_uuid.get(sos_id)
                
                if not provider_uuid:
                    logger.debug(f"Provider with NPI {npi} not found")
                    skipped_count += 1
                    continue
                    
                if not site_uuid:
                    logger.debug(f"Site with legacy ID {sos_id} not found")
                    skipped_count += 1
                    continue
                
                visits_raw = row.get('Visits', 0)
                if pd.isna(visits_raw):
                    visits_count = 0
                elif isinstance(visits_raw, str):
                    visits_count = int(visits_raw.replace(',', ''))
                else:
                    visits_count = int(visits_raw)
                
                # Check if visit record already exists
                existing_visit = session.query(ClaimsVisit).filter_by(
                    provider_id=provider_uuid,
                    site_id=site_uuid,
                    has_oncology=bool(int(row.get('visit_has_oncology', 0))),
                    has_surgery=bool(int(row.get('visit_has_surgery', 0))),
                    has_inpatient=bool(int(row.get('lead_has_inpatient', 0)))
                ).first()
                
                if existing_visit:
                    # Update existing visit count
                    existing_visit.visits += visits_count
                else:
                    # Create new visit record
                    visit = ClaimsVisit(
                        id=uuid.uuid4(),
                        provider_id=provider_uuid,
                        site_id=site_uuid,
                        visits=visits_count,
                        has_oncology=bool(int(row.get('visit_has_oncology', 0))),
                        has_surgery=bool(int(row.get('visit_has_surgery', 0))),
                        has_inpatient=bool(int(row.get('lead_has_inpatient', 0)))
                    )
                    
                    session.add(visit)
                
                imported_count += 1
                
                if imported_count % 1000 == 0:
                    logger.info(f"Processed {imported_count} visit records...")
                    session.commit()
                    
            except Exception as e:
                logger.error(f"Error importing visit record: {e}")
                session.rollback()
                skipped_count += 1
                continue
        
        session.commit()
        logger.info(f"Visit import complete. Imported: {imported_count}, Skipped: {skipped_count}")
        
    except Exception as e:
        logger.error(f"Error during visit import: {e}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    import_visits_only()