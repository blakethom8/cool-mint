from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from uuid import UUID
from sqlalchemy import select, func, and_, or_, desc, asc
from sqlalchemy.orm import Session, joinedload, selectinload

from database.data_models.email_actions import EmailAction, CallLogStaging, NoteStaging, ReminderStaging
from database.data_models.email import Email
from database.data_models.sf_models import SfUser
from database.session import get_db


class EmailActionsService:
    """Service for managing email actions and their staging data"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def list_email_actions(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        action_types: Optional[List[str]] = None,
        user_email: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        search_text: Optional[str] = None,
        sort_by: str = 'created_at',
        sort_order: str = 'desc'
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        List email actions with filtering and pagination
        
        Returns:
            Tuple of (actions list, total count)
        """
        # Base query with joins
        query = self.db.query(EmailAction).join(
            Email, EmailAction.email_id == Email.id
        ).options(
            joinedload(EmailAction.email),
            selectinload(EmailAction.call_log_staging),
            selectinload(EmailAction.note_staging),
            selectinload(EmailAction.reminder_staging)
        )
        
        # Apply filters
        if status:
            query = query.filter(EmailAction.status == status)
        
        if action_types:
            query = query.filter(EmailAction.action_type.in_(action_types))
        
        if user_email:
            query = query.filter(Email.from_email.ilike(f'%{user_email}%'))
        
        if start_date:
            query = query.filter(EmailAction.created_at >= start_date)
        
        if end_date:
            query = query.filter(EmailAction.created_at <= end_date)
        
        if search_text:
            search_pattern = f'%{search_text}%'
            query = query.filter(
                or_(
                    Email.subject.ilike(search_pattern),
                    Email.parsed_content.ilike(search_pattern),
                    EmailAction.reasoning.ilike(search_pattern)
                )
            )
        
        # Get total count
        total_count = query.count()
        
        # Apply sorting
        sort_column = getattr(EmailAction, sort_by, EmailAction.created_at)
        if sort_order == 'desc':
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))
        
        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        # Execute query and format results
        actions = query.all()
        results = []
        
        for action in actions:
            # Get staging data based on action type
            staging_data = self._get_staging_data(action)
            
            results.append({
                'id': str(action.id),
                'email_id': str(action.email_id),
                'action_type': action.action_type,
                'action_parameters': action.action_parameters,
                'confidence_score': action.confidence_score,
                'reasoning': action.reasoning,
                'status': action.status,
                'reviewed_at': action.reviewed_at.isoformat() if action.reviewed_at else None,
                'reviewed_by': action.reviewed_by,
                'review_notes': action.review_notes,
                'created_at': action.created_at.isoformat(),
                'updated_at': action.updated_at.isoformat(),
                'email': {
                    'subject': action.email.subject,
                    'from_email': action.email.from_email,
                    'to_email': action.email.to_email,
                    'date': action.email.date.isoformat() if action.email.date else None,
                    'parsed_content': action.email.parsed_content[:200] + '...' if len(action.email.parsed_content or '') > 200 else action.email.parsed_content,
                    'user_instruction': action.email.user_instruction
                },
                'staging_data': staging_data
            })
        
        return results, total_count
    
    def get_email_action_detail(self, action_id: UUID) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific email action"""
        action = self.db.query(EmailAction).options(
            joinedload(EmailAction.email),
            selectinload(EmailAction.call_log_staging),
            selectinload(EmailAction.note_staging),
            selectinload(EmailAction.reminder_staging)
        ).filter(EmailAction.id == action_id).first()
        
        if not action:
            return None
        
        staging_data = self._get_staging_data(action)
        
        return {
            'id': str(action.id),
            'email_id': str(action.email_id),
            'action_type': action.action_type,
            'action_parameters': action.action_parameters,
            'confidence_score': action.confidence_score,
            'reasoning': action.reasoning,
            'status': action.status,
            'reviewed_at': action.reviewed_at.isoformat() if action.reviewed_at else None,
            'reviewed_by': action.reviewed_by,
            'review_notes': action.review_notes,
            'executed_at': action.executed_at.isoformat() if action.executed_at else None,
            'execution_result': action.execution_result,
            'created_at': action.created_at.isoformat(),
            'updated_at': action.updated_at.isoformat(),
            'email': {
                'id': str(action.email.id),
                'subject': action.email.subject,
                'from_email': action.email.from_email,
                'to_email': action.email.to_email,
                'date': action.email.date.isoformat() if action.email.date else None,
                'content': action.email.content,
                'parsed_content': action.email.parsed_content,
                'user_instruction': action.email.user_instruction,
                'is_forwarded': action.email.is_forwarded
            },
            'staging_data': staging_data
        }
    
    def update_email_action(
        self,
        action_id: UUID,
        updates: Dict[str, Any],
        user_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """Update an email action and its staging data"""
        action = self.db.query(EmailAction).filter(EmailAction.id == action_id).first()
        
        if not action:
            return None
        
        # Update main action fields
        if 'status' in updates:
            action.status = updates['status']
        if 'review_notes' in updates:
            action.review_notes = updates['review_notes']
        
        # Track reviewer if status changed
        if user_id and 'status' in updates:
            action.reviewed_at = datetime.utcnow()
            # Get user email from SfUser
            user = self.db.query(SfUser).filter(SfUser.id == user_id).first()
            if user:
                action.reviewed_by = user.email
        
        # Update staging data if provided
        if 'staging_updates' in updates:
            self._update_staging_data(action, updates['staging_updates'])
        
        self.db.commit()
        self.db.refresh(action)
        
        return self.get_email_action_detail(action_id)
    
    def get_dashboard_stats(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Get dashboard statistics for email actions"""
        # Base query
        query = self.db.query(EmailAction)
        
        # Total counts by status
        total_pending = query.filter(EmailAction.status == 'pending').count()
        total_approved = query.filter(EmailAction.status == 'approved').count()
        total_rejected = query.filter(EmailAction.status == 'rejected').count()
        total_completed = query.filter(EmailAction.status == 'completed').count()
        
        # Counts by action type
        action_type_counts = {}
        for action_type in ['add_note', 'log_call', 'set_reminder']:
            count = query.filter(EmailAction.action_type == action_type).count()
            action_type_counts[action_type] = count
        
        # Recent activity (last 7 days)
        from datetime import timedelta
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_count = query.filter(EmailAction.created_at >= seven_days_ago).count()
        
        # Average confidence score
        avg_confidence = self.db.query(func.avg(EmailAction.confidence_score)).scalar() or 0
        
        return {
            'total_actions': query.count(),
            'pending_actions': total_pending,
            'approved_actions': total_approved,
            'rejected_actions': total_rejected,
            'completed_actions': total_completed,
            'action_type_breakdown': action_type_counts,
            'recent_actions_7_days': recent_count,
            'average_confidence_score': round(avg_confidence, 2),
            'last_updated': datetime.utcnow().isoformat()
        }
    
    def _get_staging_data(self, action: EmailAction) -> Optional[Dict[str, Any]]:
        """Get staging data based on action type"""
        if action.action_type == 'log_call' and action.call_log_staging:
            staging = action.call_log_staging[0] if action.call_log_staging else None
            if staging:
                return {
                    'type': 'call_log',
                    'id': str(staging.id),
                    'subject': staging.subject,
                    'description': staging.description,
                    'activity_date': staging.activity_date.isoformat() if staging.activity_date else None,
                    'duration_minutes': staging.duration_minutes,
                    'mno_type': staging.mno_type,
                    'mno_subtype': staging.mno_subtype,
                    'mno_setting': staging.mno_setting,
                    'contact_ids': staging.contact_ids,
                    'primary_contact_id': staging.primary_contact_id,
                    'approval_status': staging.approval_status
                }
        
        elif action.action_type == 'add_note' and action.note_staging:
            staging = action.note_staging[0] if action.note_staging else None
            if staging:
                return {
                    'type': 'note',
                    'id': str(staging.id),
                    'note_content': staging.note_content,
                    'note_type': staging.note_type,
                    'related_entity_type': staging.related_entity_type,
                    'related_entity_id': staging.related_entity_id,
                    'related_entity_name': staging.related_entity_name,
                    'approval_status': staging.approval_status
                }
        
        elif action.action_type == 'set_reminder' and action.reminder_staging:
            staging = action.reminder_staging[0] if action.reminder_staging else None
            if staging:
                return {
                    'type': 'reminder',
                    'id': str(staging.id),
                    'reminder_text': staging.reminder_text,
                    'due_date': staging.due_date.isoformat() if staging.due_date else None,
                    'priority': staging.priority,
                    'assignee': staging.assignee,
                    'assignee_id': staging.assignee_id,
                    'related_entity_type': staging.related_entity_type,
                    'related_entity_id': staging.related_entity_id,
                    'related_entity_name': staging.related_entity_name,
                    'approval_status': staging.approval_status
                }
        
        return None
    
    def _update_staging_data(self, action: EmailAction, staging_updates: Dict[str, Any]):
        """Update staging data based on action type"""
        if action.action_type == 'log_call' and action.call_log_staging:
            staging = action.call_log_staging[0]
            for field, value in staging_updates.items():
                if hasattr(staging, field):
                    setattr(staging, field, value)
            staging.user_modifications = staging_updates
        
        elif action.action_type == 'add_note' and action.note_staging:
            staging = action.note_staging[0]
            for field, value in staging_updates.items():
                if hasattr(staging, field):
                    setattr(staging, field, value)
            staging.user_modifications = staging_updates
        
        elif action.action_type == 'set_reminder' and action.reminder_staging:
            staging = action.reminder_staging[0]
            for field, value in staging_updates.items():
                if hasattr(staging, field):
                    setattr(staging, field, value)
            staging.user_modifications = staging_updates