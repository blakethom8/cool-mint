from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from uuid import UUID
from sqlalchemy import select, func, and_, or_, desc, asc
from sqlalchemy.orm import Session, joinedload, selectinload

from database.data_models.email_actions import EmailAction, CallLogStaging, NoteStaging, ReminderStaging
from database.data_models.email_data import Email


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
        # Base query with LEFT joins to handle missing emails
        query = self.db.query(EmailAction).outerjoin(
            Email, EmailAction.email_id == Email.id
        ).options(
            joinedload(EmailAction.email, innerjoin=False),
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
                    Email.body.ilike(search_pattern),
                    EmailAction.reasoning.ilike(search_pattern)
                )
            )
        
        # Get total count
        total_count = query.count()
        print(f"[DEBUG] Total email actions found: {total_count}")
        
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
        print(f"[DEBUG] Actions retrieved: {len(actions)}")
        results = []
        
        if not actions:
            print("[DEBUG] No actions found, returning empty list")
            return [], total_count
        
        for action in actions:
            try:
                # Get staging data based on action type
                staging_data = self._get_staging_data(action)
                
                print(f"[DEBUG] Processing action {action.id}, type: {action.action_type}, email_id: {action.email_id}")
                print(f"[DEBUG] Email object: {action.email}")
                
                # Build the result item
                result_item = {
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
                'updated_at': action.updated_at.isoformat()
                }
                
                # Handle date formatting - it might be an integer timestamp or datetime
                email_date = None
                if action.email and action.email.date:
                    if isinstance(action.email.date, int):
                        # Convert timestamp to datetime
                        from datetime import datetime
                        email_date = datetime.fromtimestamp(action.email.date).isoformat()
                    elif hasattr(action.email.date, 'isoformat'):
                        email_date = action.email.date.isoformat()
                    else:
                        email_date = str(action.email.date)
                
                result_item['email'] = {
                    'subject': action.email.subject if action.email else 'No subject',
                    'from_email': action.email.from_email if action.email else 'Unknown',
                    'to_email': action.email.to_emails if action.email else None,
                    'date': email_date,
                    'parsed_content': (action.email.body[:200] + '...' if action.email and action.email.body and len(action.email.body) > 200 else action.email.body if action.email else None),
                    'user_instruction': action.email.user_instruction if action.email else None
                }
                result_item['staging_data'] = staging_data
                
                print(f"[DEBUG] Successfully built result item for action {action.id}")
                results.append(result_item)
            except Exception as e:
                print(f"[DEBUG] Error processing action {action.id}: {str(e)}")
                import traceback
                traceback.print_exc()
                continue
        
        print(f"[DEBUG] Returning {len(results)} results")
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
        
        # Handle date formatting for detail endpoint
        email_date = None
        if action.email and action.email.date:
            if isinstance(action.email.date, int):
                # Convert timestamp to datetime
                from datetime import datetime as dt
                email_date = dt.fromtimestamp(action.email.date).isoformat()
            elif hasattr(action.email.date, 'isoformat'):
                email_date = action.email.date.isoformat()
            else:
                email_date = str(action.email.date)
        
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
                'id': str(action.email.id) if action.email else None,
                'subject': action.email.subject if action.email else 'No subject',
                'from_email': action.email.from_email if action.email else 'Unknown',
                'to_email': action.email.to_emails if action.email else None,
                'date': email_date,
                'content': action.email.body if action.email else None,
                'parsed_content': action.email.body if action.email else None,  # Use body field
                'user_instruction': action.email.user_instruction if action.email else None,
                'is_forwarded': action.email.is_forwarded if action.email else False
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
        if 'status' in updates:
            action.reviewed_at = datetime.utcnow()
            # For now, just mark as reviewed by system
            action.reviewed_by = 'system' if not user_id else f'user_{user_id}'
        
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
        try:
            if action.action_type == 'log_call' and hasattr(action, 'call_log_staging') and action.call_log_staging:
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
            
            elif action.action_type == 'add_note' and hasattr(action, 'note_staging') and action.note_staging:
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
            
            elif action.action_type == 'set_reminder' and hasattr(action, 'reminder_staging') and action.reminder_staging:
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
        except Exception as e:
            print(f"[DEBUG] Error getting staging data: {e}")
            return None
        
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