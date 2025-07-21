"""
Relationship Management Service

Handles business logic for relationship CRUD operations, filtering,
and related data retrieval.
"""

from datetime import datetime, date, timedelta, timezone
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
from sqlalchemy import select, func, and_, or_, text
from sqlalchemy.orm import Session, selectinload, joinedload

from database.data_models.relationship_management import (
    Relationships, Campaigns, CampaignRelationships,
    RelationshipHistory, RelationshipMetrics
)
from database.data_models.crm_lookups import (
    RelationshipStatusTypes, LoyaltyStatusTypes, EntityTypes
)
from database.data_models.salesforce_data import SfUser, SfContact, SfActivityStructured
from database.data_models.claims_data import ClaimsProvider, SiteOfService
from schemas.relationship_schema import (
    RelationshipListItem, RelationshipDetail, RelationshipFilters,
    RelationshipUpdate, ActivityLogCreate, RelationshipMetrics as MetricsSchema,
    EntityTypeInfo, RelationshipStatusInfo, LoyaltyStatusInfo,
    ActivityLogItem, CampaignInfo
)


class RelationshipService:
    """Service for managing relationships."""
    
    def __init__(self, db: Session):
        self.db = db
        
    def list_relationships(
        self,
        filters: RelationshipFilters,
        page: int = 1,
        page_size: int = 50,
        sort_by: str = "last_activity_date",
        sort_order: str = "desc"
    ) -> Tuple[List[RelationshipListItem], int]:
        """
        List relationships with filtering and pagination.
        
        Returns tuple of (items, total_count)
        """
        # Base query with eager loading
        query = self.db.query(Relationships).options(
            joinedload(Relationships.user),
            joinedload(Relationships.entity_type),
            joinedload(Relationships.relationship_status_type),
            joinedload(Relationships.loyalty_status_type)
        )
        
        # Apply filters
        query = self._apply_filters(query, filters)
        
        # Get total count
        total_count = query.count()
        
        # Apply sorting
        sort_column = getattr(Relationships, sort_by, Relationships.last_activity_date)
        if sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
            
        # Apply pagination
        offset = (page - 1) * page_size
        relationships = query.offset(offset).limit(page_size).all()
        
        # Convert to response items
        items = []
        for rel in relationships:
            # Get entity details based on type
            entity_details = self._get_entity_details(rel.entity_type.code, rel.linked_entity_id)
            
            # Calculate days since activity
            days_since = None
            if rel.last_activity_date:
                # Handle both timezone-aware and naive datetimes
                now = datetime.now()
                if rel.last_activity_date.tzinfo is not None:
                    # If the stored date is timezone-aware, make 'now' aware too
                    now = datetime.now(timezone.utc)
                days_since = (now - rel.last_activity_date).days
            
            # Get activity count (simplified for now)
            activity_count = self._get_activity_count(rel.relationship_id)
            
            # Get campaign count
            campaign_count = self.db.query(CampaignRelationships).filter(
                CampaignRelationships.relationship_id == rel.relationship_id
            ).count()
            
            item = RelationshipListItem(
                relationship_id=rel.relationship_id,
                user_id=rel.user_id,
                user_name=rel.user.name,
                entity_type=EntityTypeInfo(
                    id=rel.entity_type.id,
                    code=rel.entity_type.code,
                    common_name=rel.entity_type.common_name
                ),
                linked_entity_id=rel.linked_entity_id,
                entity_name=entity_details.get('name', 'Unknown'),
                entity_details=entity_details,
                relationship_status=RelationshipStatusInfo(
                    id=rel.relationship_status_type.id,
                    code=rel.relationship_status_type.code,
                    display_name=rel.relationship_status_type.display_name
                ),
                loyalty_status=LoyaltyStatusInfo(
                    id=rel.loyalty_status_type.id,
                    code=rel.loyalty_status_type.code,
                    display_name=rel.loyalty_status_type.display_name,
                    color_hex=rel.loyalty_status_type.color_hex
                ) if rel.loyalty_status_type else None,
                lead_score=rel.lead_score,
                last_activity_date=rel.last_activity_date,
                days_since_activity=days_since,
                engagement_frequency=rel.engagement_frequency,
                activity_count=activity_count,
                campaign_count=campaign_count,
                next_steps=rel.next_steps,
                created_at=rel.created_at,
                updated_at=rel.updated_at
            )
            items.append(item)
            
        return items, total_count
    
    def get_relationship_detail(self, relationship_id: UUID) -> Optional[RelationshipDetail]:
        """Get detailed information for a specific relationship."""
        rel = self.db.query(Relationships).options(
            joinedload(Relationships.user),
            joinedload(Relationships.entity_type),
            joinedload(Relationships.relationship_status_type),
            joinedload(Relationships.loyalty_status_type),
            selectinload(Relationships.campaign_relationships).joinedload(CampaignRelationships.campaign)
        ).filter(Relationships.relationship_id == relationship_id).first()
        
        if not rel:
            return None
            
        # Get entity details
        entity_details = self._get_entity_details(rel.entity_type.code, rel.linked_entity_id)
        
        # Get recent activities
        recent_activities = self._get_recent_activities(rel.user_id, rel.linked_entity_id, limit=10)
        
        # Get metrics
        metrics = self._calculate_metrics(rel.relationship_id, rel.user_id, rel.linked_entity_id)
        
        # Get campaigns
        campaigns = []
        for cr in rel.campaign_relationships:
            campaigns.append(CampaignInfo(
                campaign_id=cr.campaign.campaign_id,
                campaign_name=cr.campaign.campaign_name,
                status=cr.campaign.status,
                start_date=cr.campaign.start_date,
                end_date=cr.campaign.end_date
            ))
        
        return RelationshipDetail(
            relationship_id=rel.relationship_id,
            user_id=rel.user_id,
            user_name=rel.user.name,
            user_email=rel.user.email,
            entity_type=EntityTypeInfo(
                id=rel.entity_type.id,
                code=rel.entity_type.code,
                common_name=rel.entity_type.common_name
            ),
            linked_entity_id=rel.linked_entity_id,
            entity_name=entity_details.get('name', 'Unknown'),
            entity_details=entity_details,
            relationship_status=RelationshipStatusInfo(
                id=rel.relationship_status_type.id,
                code=rel.relationship_status_type.code,
                display_name=rel.relationship_status_type.display_name
            ),
            loyalty_status=LoyaltyStatusInfo(
                id=rel.loyalty_status_type.id,
                code=rel.loyalty_status_type.code,
                display_name=rel.loyalty_status_type.display_name,
                color_hex=rel.loyalty_status_type.color_hex
            ) if rel.loyalty_status_type else None,
            lead_score=rel.lead_score,
            last_activity_date=rel.last_activity_date,
            next_steps=rel.next_steps,
            engagement_frequency=rel.engagement_frequency,
            campaigns=campaigns,
            metrics=metrics,
            recent_activities=recent_activities,
            created_at=rel.created_at,
            updated_at=rel.updated_at
        )
    
    def update_relationship(
        self,
        relationship_id: UUID,
        updates: RelationshipUpdate,
        user_id: int
    ) -> Optional[RelationshipListItem]:
        """Update a relationship and track history."""
        rel = self.db.query(Relationships).filter(
            Relationships.relationship_id == relationship_id
        ).first()
        
        if not rel:
            return None
            
        # Track changes for history
        changes_made = False
        old_status_id = rel.relationship_status_id
        old_loyalty_id = rel.loyalty_status_id
        
        # Apply updates
        if updates.relationship_status_id is not None and updates.relationship_status_id != rel.relationship_status_id:
            rel.relationship_status_id = updates.relationship_status_id
            changes_made = True
            
        if updates.loyalty_status_id is not None and updates.loyalty_status_id != rel.loyalty_status_id:
            rel.loyalty_status_id = updates.loyalty_status_id
            changes_made = True
            
        if updates.lead_score is not None:
            rel.lead_score = updates.lead_score
            
        if updates.next_steps is not None:
            rel.next_steps = updates.next_steps
            
        if updates.engagement_frequency is not None:
            rel.engagement_frequency = updates.engagement_frequency
            
        rel.updated_at = datetime.now()
        
        # Create history record if status changed
        if changes_made:
            history = RelationshipHistory(
                relationship_id=relationship_id,
                changed_by_user_id=user_id,
                previous_relationship_status=self._get_status_code(old_status_id),
                new_relationship_status=self._get_status_code(rel.relationship_status_id),
                previous_loyalty=self._get_loyalty_code(old_loyalty_id),
                new_loyalty=self._get_loyalty_code(rel.loyalty_status_id),
                change_reason="Manual update via UI"
            )
            self.db.add(history)
        
        self.db.commit()
        self.db.refresh(rel)
        
        # Return updated item
        return self.get_relationship_detail(relationship_id)
    
    def get_filter_options(self, current_user_id: Optional[int] = None) -> Dict[str, Any]:
        """Get available filter options for dropdowns."""
        # Get users with relationship counts
        users_query = self.db.query(
            SfUser.id,
            SfUser.name,
            func.count(Relationships.relationship_id).label('count')
        ).join(
            Relationships, Relationships.user_id == SfUser.id
        ).group_by(SfUser.id, SfUser.name).all()
        
        users = [
            {"id": u.id, "name": u.name, "relationship_count": u.count}
            for u in users_query
        ]
        
        # Get entity types
        entity_types = self.db.query(EntityTypes).filter(
            EntityTypes.is_active == True
        ).order_by(EntityTypes.sort_order).all()
        
        # Get statuses
        rel_statuses = self.db.query(RelationshipStatusTypes).filter(
            RelationshipStatusTypes.is_active == True
        ).order_by(RelationshipStatusTypes.sort_order).all()
        
        loyalty_statuses = self.db.query(LoyaltyStatusTypes).filter(
            LoyaltyStatusTypes.is_active == True
        ).order_by(LoyaltyStatusTypes.sort_order).all()
        
        # Get active campaigns
        campaigns_query = self.db.query(
            Campaigns.campaign_id,
            Campaigns.campaign_name
        ).filter(
            Campaigns.status == 'Active'
        ).all()
        
        campaigns = [
            {"id": str(c.campaign_id), "name": c.campaign_name}
            for c in campaigns_query
        ]
        
        # Get unique specialties from contacts
        specialties = self.db.query(
            func.distinct(SfContact.mn_specialty_group)
        ).filter(
            SfContact.mn_specialty_group.isnot(None)
        ).all()
        
        # Get unique geographies
        geographies = self.db.query(
            func.distinct(SfContact.mn_primary_geography)
        ).filter(
            SfContact.mn_primary_geography.isnot(None)
        ).all()
        
        return {
            "users": users,
            "entity_types": [EntityTypeInfo(
                id=et.id,
                code=et.code,
                common_name=et.common_name
            ) for et in entity_types],
            "relationship_statuses": [RelationshipStatusInfo(
                id=rs.id,
                code=rs.code,
                display_name=rs.display_name
            ) for rs in rel_statuses],
            "loyalty_statuses": [LoyaltyStatusInfo(
                id=ls.id,
                code=ls.code,
                display_name=ls.display_name,
                color_hex=ls.color_hex
            ) for ls in loyalty_statuses],
            "campaigns": campaigns,
            "specialties": [s[0] for s in specialties if s[0]],
            "geographies": [g[0] for g in geographies if g[0]]
        }
    
    # Private helper methods
    def _apply_filters(self, query, filters: RelationshipFilters):
        """Apply filters to the query."""
        if filters.user_ids:
            query = query.filter(Relationships.user_id.in_(filters.user_ids))
            
        if filters.entity_type_ids:
            query = query.filter(Relationships.entity_type_id.in_(filters.entity_type_ids))
            
        if filters.relationship_status_ids:
            query = query.filter(Relationships.relationship_status_id.in_(filters.relationship_status_ids))
            
        if filters.loyalty_status_ids:
            query = query.filter(Relationships.loyalty_status_id.in_(filters.loyalty_status_ids))
            
        if filters.lead_scores:
            query = query.filter(Relationships.lead_score.in_(filters.lead_scores))
            
        if filters.last_activity_after:
            query = query.filter(Relationships.last_activity_date >= filters.last_activity_after)
            
        if filters.last_activity_before:
            query = query.filter(Relationships.last_activity_date <= filters.last_activity_before)
            
        if filters.search_text:
            # This would need to be enhanced to search entity names
            query = query.filter(
                or_(
                    Relationships.next_steps.ilike(f"%{filters.search_text}%"),
                    # Add more search fields as needed
                )
            )
            
        return query
    
    def _get_entity_details(self, entity_type_code: str, entity_id: UUID) -> Dict[str, Any]:
        """Get details for an entity based on its type."""
        if entity_type_code == "SfContact":
            contact = self.db.query(SfContact).filter(
                SfContact.id == entity_id
            ).first()
            if contact:
                return {
                    "name": contact.name,
                    "email": contact.email,
                    "phone": contact.phone,
                    "specialty": contact.mn_specialty_group,
                    "geography": contact.mn_primary_geography,
                    "title": contact.title,
                    "account": contact.contact_account_name,
                    "employment_status": contact.employment_status_mn,
                    "provider_group": contact.contact_account_name  # Using account name as provider group
                }
        elif entity_type_code == "ClaimsProvider":
            provider = self.db.query(ClaimsProvider).filter(
                ClaimsProvider.id == entity_id
            ).first()
            if provider:
                return {
                    "name": provider.name,
                    "npi": provider.npi,
                    "specialty": provider.specialty,
                    "city": provider.city,
                    "state": provider.state
                }
        elif entity_type_code == "SiteOfService":
            site = self.db.query(SiteOfService).filter(
                SiteOfService.id == entity_id
            ).first()
            if site:
                return {
                    "name": site.name,
                    "city": site.city,
                    "state": site.county,  # Using county since state is not available
                    "site_type": site.site_type
                }
        
        return {"name": "Unknown"}
    
    def _get_activity_count(self, relationship_id: UUID) -> int:
        """Get count of activities for a relationship."""
        # Get the relationship to find user and contact
        rel = self.db.query(Relationships).filter(
            Relationships.relationship_id == relationship_id
        ).first()
        
        if not rel:
            return 0
            
        # Get user's salesforce ID
        user_result = self.db.execute(text(
            "SELECT salesforce_id FROM sf_users WHERE id = :user_id"
        ), {"user_id": rel.user_id}).first()
        
        if not user_result:
            return 0
            
        # Get contact's name
        contact_result = self.db.execute(text(
            "SELECT name FROM sf_contacts WHERE id = :contact_id"
        ), {"contact_id": str(rel.linked_entity_id)}).first()
        
        if not contact_result:
            return 0
            
        # Count activities
        result = self.db.execute(text("""
            SELECT COUNT(*) as count
            FROM sf_activities_structured
            WHERE owner_id = :owner_id
            AND :contact_name = ANY(contact_names)
        """), {
            "owner_id": user_result.salesforce_id,
            "contact_name": contact_result.name
        }).first()
        
        return result.count if result else 0
    
    def _get_recent_activities(
        self, 
        user_id: int, 
        contact_id: UUID, 
        limit: int = 10
    ) -> List[ActivityLogItem]:
        """Get recent activities between user and contact."""
        activities = []
        
        try:
            # Get user's salesforce ID
            user_result = self.db.execute(text(
                "SELECT salesforce_id FROM sf_users WHERE id = :user_id"
            ), {"user_id": user_id}).first()
            
            if not user_result:
                return activities
                
            # Get contact's salesforce ID and name
            contact_result = self.db.execute(text(
                "SELECT salesforce_id, name FROM sf_contacts WHERE id = :contact_id"
            ), {"contact_id": str(contact_id)}).first()
            
            if not contact_result:
                return activities
            
            user_sf_id = user_result.salesforce_id
            contact_name = contact_result.name
            
            # Query activities using contact_names array (simpler approach)
            results = self.db.execute(text("""
                SELECT 
                    id,
                    activity_date,
                    subject,
                    description,
                    type,
                    mno_type,
                    mno_subtype,
                    status,
                    user_name,
                    contact_names
                FROM sf_activities_structured
                WHERE owner_id = :owner_id
                AND :contact_name = ANY(contact_names)
                ORDER BY activity_date DESC
                LIMIT :limit
            """), {
                "owner_id": user_sf_id,
                "contact_name": contact_name,
                "limit": limit
            })
            
            for row in results:
                # Convert date to datetime for consistency
                activity_datetime = datetime.combine(
                    row.activity_date, 
                    datetime.min.time()
                ).replace(tzinfo=timezone.utc) if row.activity_date else datetime.now(timezone.utc)
                
                activities.append(ActivityLogItem(
                    activity_id=str(row.id),
                    activity_date=activity_datetime,
                    subject=row.subject or "No subject",
                    description=row.description,
                    activity_type=row.type or "Activity",
                    mno_type=row.mno_type,
                    mno_subtype=row.mno_subtype,
                    status=row.status or "Completed",
                    owner_name=row.user_name,
                    contact_names=row.contact_names or []
                ))
                
        except Exception as e:
            print(f"Error fetching activities: {e}")
            # Return empty list on error
            
        return activities
    
    def _calculate_metrics(
        self,
        relationship_id: UUID,
        user_id: int,
        contact_id: UUID
    ) -> MetricsSchema:
        """Calculate relationship metrics."""
        # This is a simplified version - would expand with real activity data
        today = date.today()
        
        # Get existing metrics if any
        latest_metric = self.db.query(RelationshipMetrics).filter(
            RelationshipMetrics.relationship_id == relationship_id
        ).order_by(RelationshipMetrics.metric_date.desc()).first()
        
        if latest_metric:
            return MetricsSchema(
                total_activities=latest_metric.meetings_count + latest_metric.calls_count + latest_metric.emails_count,
                activities_last_30_days=0,  # Would calculate from activities
                activities_last_90_days=0,
                average_days_between_activities=None,
                most_common_activity_type="Meeting",
                last_activity_days_ago=None,
                referral_count=latest_metric.referrals_count,
                meeting_count=latest_metric.meetings_count,
                call_count=latest_metric.calls_count,
                email_count=latest_metric.emails_count
            )
        
        # Default metrics
        return MetricsSchema(
            total_activities=0,
            activities_last_30_days=0,
            activities_last_90_days=0,
            average_days_between_activities=None,
            most_common_activity_type=None,
            last_activity_days_ago=None,
            referral_count=0,
            meeting_count=0,
            call_count=0,
            email_count=0
        )
    
    def _get_status_code(self, status_id: Optional[int]) -> Optional[str]:
        """Get status code by ID."""
        if not status_id:
            return None
        status = self.db.query(RelationshipStatusTypes.code).filter(
            RelationshipStatusTypes.id == status_id
        ).first()
        return status.code if status else None
    
    def _get_loyalty_code(self, loyalty_id: Optional[int]) -> Optional[str]:
        """Get loyalty code by ID."""
        if not loyalty_id:
            return None
        loyalty = self.db.query(LoyaltyStatusTypes.code).filter(
            LoyaltyStatusTypes.id == loyalty_id
        ).first()
        return loyalty.code if loyalty else None