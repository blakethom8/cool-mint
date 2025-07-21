"""
Relationship Seeding Service

This service handles the one-time seeding of the relationships table
based on historical activity data from sf_activities_structured.
"""

from datetime import datetime, timedelta
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Optional, Set
import logging
from uuid import UUID, uuid4
from sqlalchemy import text, and_, or_, func
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert

from database.session import SessionLocal
from database.data_models.relationship_management import Relationships
from database.data_models.crm_lookups import RelationshipStatusTypes, LoyaltyStatusTypes, EntityTypes
from database.data_models.salesforce_data import SfUser, SfContact

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RelationshipSeedingService:
    """Service to seed relationships table from activity data."""
    
    def __init__(self, db: Session):
        self.db = db
        self.status_map = {}
        self.loyalty_map = {}
        self.entity_type_map = {}
        self._load_lookup_data()
        
    def _load_lookup_data(self):
        """Load lookup table data into memory for efficient access."""
        # Load relationship status types
        statuses = self.db.query(RelationshipStatusTypes).all()
        self.status_map = {status.code: status.id for status in statuses}
        logger.info(f"Loaded {len(self.status_map)} relationship status types")
        
        # Load loyalty status types
        loyalties = self.db.query(LoyaltyStatusTypes).all()
        self.loyalty_map = {loyalty.code: loyalty.id for loyalty in loyalties}
        logger.info(f"Loaded {len(self.loyalty_map)} loyalty status types")
        
        # Load entity types
        entity_types = self.db.query(EntityTypes).all()
        self.entity_type_map = {et.code: et.id for et in entity_types}
        logger.info(f"Loaded {len(self.entity_type_map)} entity types")
    
    def extract_unique_relationships(self, 
                                   include_employed: bool = True,
                                   include_community: bool = True) -> Dict[Tuple[str, str], Dict]:
        """
        Extract unique user-contact relationships from activity data.
        
        Args:
            include_employed: Include contacts with Employed status
            include_community: Include contacts with Community/Out of Network status
            
        Returns:
            Dictionary keyed by (owner_id, contact_id) tuples
        """
        logger.info("Extracting unique relationships from activities...")
        
        # Query all activities with JSON data
        activities = self.db.execute(text("""
            SELECT 
                owner_id,
                activity_date,
                llm_context_json,
                mno_type,
                mno_subtype,
                priority
            FROM sf_activities_structured
            WHERE llm_context_json IS NOT NULL
            ORDER BY activity_date DESC
        """)).fetchall()
        
        relationships = defaultdict(lambda: {
            'activities': [],
            'employment_statuses': set(),
            'is_physician': False,
            'specialties': set(),
            'contact_name': None,
            'contact_sf_id': None,
            'last_activity': None,
            'first_activity': None,
            'activity_count': 0,
            'mno_types': Counter(),
            'high_priority_count': 0,
            'last_90_days_count': 0,
            'recent_subjects': []
        })
        
        today = datetime.now().date()
        ninety_days_ago = today - timedelta(days=90)
        
        for activity in activities:
            if not activity.llm_context_json or 'contacts' not in activity.llm_context_json:
                continue
                
            for contact in activity.llm_context_json['contacts']:
                contact_sf_id = contact.get('contact_id')
                if not contact_sf_id:
                    continue
                
                # Check employment status filter
                employment_status = contact.get('employment_status', 'Unknown')
                if employment_status == 'Employed' and not include_employed:
                    continue
                if employment_status in ['Community', 'Out of Network'] and not include_community:
                    continue
                    
                key = (activity.owner_id, contact_sf_id)
                rel = relationships[key]
                
                # Track activity details
                rel['activities'].append(activity.activity_date)
                rel['activity_count'] += 1
                rel['mno_types'][activity.mno_type] += 1
                
                # Track high priority activities
                if activity.priority == 'High':
                    rel['high_priority_count'] += 1
                
                # Count activities in last 90 days
                if activity.activity_date >= ninety_days_ago:
                    rel['last_90_days_count'] += 1
                
                # Track contact details
                rel['employment_statuses'].add(employment_status)
                rel['is_physician'] = contact.get('is_physician', False)
                if contact.get('mn_specialty_group'):
                    rel['specialties'].add(contact['mn_specialty_group'])
                rel['contact_name'] = contact.get('contact_name')
                rel['contact_sf_id'] = contact_sf_id
                
                # Update date range
                if not rel['first_activity'] or activity.activity_date < rel['first_activity']:
                    rel['first_activity'] = activity.activity_date
                if not rel['last_activity'] or activity.activity_date > rel['last_activity']:
                    rel['last_activity'] = activity.activity_date
                
                # Track recent subjects
                if len(rel['recent_subjects']) < 5 and activity.llm_context_json.get('subject'):
                    rel['recent_subjects'].append(activity.llm_context_json['subject'])
        
        logger.info(f"Found {len(relationships)} unique user-contact relationships")
        return dict(relationships)
    
    def calculate_relationship_status(self, relationship_data: Dict) -> int:
        """
        Calculate relationship status based on activity patterns.
        
        Business Rules:
        - ESTABLISHED: >5 activities in last 90 days
        - BUILDING: 2-5 activities in last 90 days  
        - PROSPECTING: 1 activity in last 90 days or older
        - DEPRIORITIZED: No activity in 180+ days
        """
        today = datetime.now().date()
        days_since_last = (today - relationship_data['last_activity']).days
        recent_count = relationship_data['last_90_days_count']
        
        if days_since_last > 180:
            return self.status_map['DEPRIORITIZED']
        elif recent_count > 5:
            return self.status_map['ESTABLISHED']
        elif recent_count >= 2:
            return self.status_map['BUILDING']
        else:
            return self.status_map['PROSPECTING']
    
    def calculate_lead_score(self, relationship_data: Dict) -> int:
        """
        Calculate lead score (1-5) based on activity patterns.
        
        Scoring factors:
        - Activity frequency
        - Recency
        - High priority activities
        - Employment status (Community contacts score higher)
        """
        score = 3  # Start with neutral score
        
        # Frequency bonus
        if relationship_data['activity_count'] >= 10:
            score += 1
        elif relationship_data['activity_count'] <= 1:
            score -= 1
            
        # Recency bonus
        days_since = (datetime.now().date() - relationship_data['last_activity']).days
        if days_since <= 30:
            score += 1
        elif days_since > 180:
            score -= 1
            
        # Priority bonus
        if relationship_data['high_priority_count'] >= 3:
            score += 1
            
        # Employment status consideration
        if 'Community' in relationship_data['employment_statuses'] or \
           'Out of Network' in relationship_data['employment_statuses']:
            score += 1
            
        # Ensure score is within bounds
        return max(1, min(5, score))
    
    def calculate_engagement_frequency(self, relationship_data: Dict) -> Optional[str]:
        """
        Calculate expected engagement frequency based on activity patterns.
        """
        if relationship_data['activity_count'] < 2:
            return None
            
        # Calculate average days between activities
        activities = sorted(relationship_data['activities'])
        gaps = []
        for i in range(1, len(activities)):
            gap = (activities[i] - activities[i-1]).days
            gaps.append(gap)
        
        if not gaps:
            return None
            
        avg_gap = sum(gaps) / len(gaps)
        
        if avg_gap <= 7:
            return 'Weekly'
        elif avg_gap <= 30:
            return 'Monthly'
        elif avg_gap <= 90:
            return 'Quarterly'
        else:
            return 'Sporadic'
    
    def create_relationship_records(self, relationships: Dict[Tuple[str, str], Dict]) -> int:
        """
        Create relationship records in the database.
        
        Returns:
            Number of relationships created
        """
        logger.info("Creating relationship records...")
        
        # Get entity type for SfContact
        sf_contact_type_id = self.entity_type_map['SfContact']
        
        # Prepare data for bulk insert
        records_to_insert = []
        skipped_contacts = []
        skipped_users = []
        
        for (owner_sf_id, contact_sf_id), rel_data in relationships.items():
            # Look up user ID
            user = self.db.query(SfUser.id).filter(
                SfUser.salesforce_id == owner_sf_id
            ).first()
            
            if not user:
                skipped_users.append(owner_sf_id)
                continue
                
            # Look up contact ID
            contact = self.db.query(SfContact.id).filter(
                SfContact.salesforce_id == contact_sf_id
            ).first()
            
            if not contact:
                skipped_contacts.append(contact_sf_id)
                continue
            
            # Calculate fields
            relationship_status_id = self.calculate_relationship_status(rel_data)
            lead_score = self.calculate_lead_score(rel_data)
            engagement_frequency = self.calculate_engagement_frequency(rel_data)
            
            # Default loyalty status to UNKNOWN
            loyalty_status_id = self.loyalty_map['UNKNOWN']
            
            # Prepare next steps based on status
            if relationship_status_id == self.status_map['DEPRIORITIZED']:
                next_steps = "Re-engage with touchpoint to reactivate relationship"
            elif relationship_status_id == self.status_map['PROSPECTING']:
                next_steps = "Schedule follow-up meeting to build rapport"
            elif relationship_status_id == self.status_map['BUILDING']:
                next_steps = "Continue regular engagement, identify specific needs"
            else:  # ESTABLISHED
                next_steps = "Maintain relationship, explore referral opportunities"
            
            record = {
                'relationship_id': uuid4(),
                'user_id': user.id,
                'entity_type_id': sf_contact_type_id,
                'linked_entity_id': contact.id,
                'relationship_status_id': relationship_status_id,
                'loyalty_status_id': loyalty_status_id,
                'lead_score': lead_score,
                'last_activity_date': datetime.combine(rel_data['last_activity'], datetime.min.time()),
                'next_steps': next_steps,
                'engagement_frequency': engagement_frequency,
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
            
            records_to_insert.append(record)
        
        # Log skipped records
        if skipped_users:
            logger.warning(f"Skipped {len(set(skipped_users))} unknown users")
        if skipped_contacts:
            logger.warning(f"Skipped {len(set(skipped_contacts))} unknown contacts")
        
        # Bulk insert relationships
        if records_to_insert:
            # Check for existing relationships first
            created_count = 0
            updated_count = 0
            
            for record in records_to_insert:
                # Check if relationship exists
                existing = self.db.query(Relationships).filter(
                    and_(
                        Relationships.user_id == record['user_id'],
                        Relationships.entity_type_id == record['entity_type_id'],
                        Relationships.linked_entity_id == record['linked_entity_id']
                    )
                ).first()
                
                if existing:
                    # Update existing relationship
                    existing.last_activity_date = record['last_activity_date']
                    existing.relationship_status_id = record['relationship_status_id']
                    existing.lead_score = record['lead_score']
                    existing.engagement_frequency = record['engagement_frequency']
                    existing.updated_at = datetime.now()
                    updated_count += 1
                else:
                    # Create new relationship
                    new_rel = Relationships(**record)
                    self.db.add(new_rel)
                    created_count += 1
            
            self.db.commit()
            logger.info(f"Created {created_count} new relationships, updated {updated_count} existing")
            
            logger.info(f"Successfully created/updated {len(records_to_insert)} relationships")
        
        return len(records_to_insert)
    
    def generate_summary_report(self, relationships: Dict[Tuple[str, str], Dict]) -> Dict:
        """Generate a summary report of the seeding process."""
        today = datetime.now().date()
        
        # Calculate various metrics
        total_relationships = len(relationships)
        employed_only = sum(1 for r in relationships.values() 
                          if all(s == 'Employed' for s in r['employment_statuses']))
        community_any = sum(1 for r in relationships.values() 
                          if any(s in ['Community', 'Out of Network'] 
                                for s in r['employment_statuses']))
        
        # Activity metrics
        active_90_days = sum(1 for r in relationships.values() 
                           if (today - r['last_activity']).days <= 90)
        
        # Status distribution
        status_dist = Counter()
        for rel_data in relationships.values():
            status_id = self.calculate_relationship_status(rel_data)
            status_name = next(k for k, v in self.status_map.items() if v == status_id)
            status_dist[status_name] += 1
        
        report = {
            'total_relationships': total_relationships,
            'employed_only_count': employed_only,
            'community_involved_count': community_any,
            'active_last_90_days': active_90_days,
            'status_distribution': dict(status_dist),
            'timestamp': datetime.now().isoformat()
        }
        
        return report
    
    def seed_relationships(self, include_employed: bool = True, 
                         include_community: bool = True) -> Dict:
        """
        Main method to seed relationships table.
        
        Args:
            include_employed: Include employed contacts
            include_community: Include community contacts
            
        Returns:
            Summary report dictionary
        """
        logger.info("Starting relationship seeding process...")
        
        # Extract relationships
        relationships = self.extract_unique_relationships(
            include_employed=include_employed,
            include_community=include_community
        )
        
        # Create records
        created_count = self.create_relationship_records(relationships)
        
        # Generate report
        report = self.generate_summary_report(relationships)
        report['records_created'] = created_count
        
        logger.info("Relationship seeding completed!")
        logger.info(f"Summary: {report}")
        
        return report


# Convenience function for running the seeding
def run_seeding(include_employed: bool = True, include_community: bool = True):
    """Run the relationship seeding process."""
    db = SessionLocal()
    try:
        service = RelationshipSeedingService(db)
        report = service.seed_relationships(
            include_employed=include_employed,
            include_community=include_community
        )
        return report
    finally:
        db.close()


if __name__ == "__main__":
    # Run seeding when script is executed directly
    report = run_seeding()
    print("\nSeeding Report:")
    for key, value in report.items():
        print(f"{key}: {value}")