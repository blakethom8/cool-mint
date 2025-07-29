from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from uuid import UUID
from sqlalchemy import select, func, and_, or_, desc, asc
from sqlalchemy.orm import Session, joinedload, selectinload

from database.data_models.email_actions import EmailAction, CallLogStaging, NoteStaging, ReminderStaging
from database.data_models.email_data import Email
from database.data_models.salesforce_data import SfActivityStructured
from database.data_models.crm_general import Notes
from database.data_models.relationship_management import Reminders


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
    
    def transfer_call_log_to_activity(
        self,
        staging_id: UUID,
        user_id: str,
        final_values: Dict[str, Any],
        additional_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Transfer a call log from staging to sf_activities_structured table.
        
        Creates a new structured activity record and updates the staging record
        with the transfer status and relationship.
        """
        # Get the staging record
        staging = self.db.query(CallLogStaging).filter(CallLogStaging.id == staging_id).first()
        if not staging:
            raise ValueError(f"Call log staging record {staging_id} not found")
        
        # Check if already transferred
        if staging.transferred_to_activity_id:
            raise ValueError(f"Call log staging record {staging_id} has already been transferred")
        
        # Parse activity date if it's a string
        activity_date = final_values.get('activity_date') or staging.activity_date
        if isinstance(activity_date, str):
            try:
                # Handle ISO format from frontend
                activity_date = datetime.fromisoformat(activity_date.replace('Z', '+00:00'))
            except:
                activity_date = datetime.utcnow()
        elif not activity_date:
            activity_date = datetime.utcnow()
            
        print(f"[DEBUG] Creating activity with date: {activity_date}")
        
        # Create structured activity record using final values from user
        structured_activity = SfActivityStructured(
            activity_date=activity_date,
            subject=final_values.get('subject', staging.subject),
            description=final_values.get('description', staging.description),
            status='Completed',
            priority=final_values.get('priority', 'Normal'),
            mno_type=final_values.get('mno_type', staging.mno_type),
            mno_subtype=final_values.get('mno_subtype', staging.mno_subtype),
            mno_setting=final_values.get('mno_setting', staging.mno_setting),
            type='Task',
            owner_id=user_id,
            user_name=additional_data.get('user_name', '') if additional_data else '',
            
            # Contact information from final values
            contact_count=len(final_values.get('contact_ids', staging.contact_ids or [])),
            contact_names=final_values.get('contact_ids', staging.contact_ids if isinstance(staging.contact_ids, list) else []),
            
            # Required fields
            salesforce_activity_id=f'STG_{str(staging_id)[:14]}',  # Temporary ID (max 18 chars)
            source_activity_id=None,  # No SF activity record for email actions
            
            # LLM context with delta tracking
            llm_context_json={
                'staging_id': str(staging_id),
                'email_action_id': str(staging.email_action_id),
                'original_llm_values': {
                    'subject': staging.subject,
                    'description': staging.description,
                    'activity_date': staging.activity_date.isoformat() if staging.activity_date else None,
                    'mno_type': staging.mno_type,
                    'mno_subtype': staging.mno_subtype,
                    'mno_setting': staging.mno_setting,
                    'contacts': staging.contact_ids,
                    'suggested_values': staging.suggested_values
                },
                'user_final_values': final_values,
                'delta_summary': {
                    'subject_changed': final_values.get('subject') != staging.subject,
                    'description_changed': final_values.get('description') != staging.description,
                    'date_changed': final_values.get('activity_date') != staging.activity_date,
                    'type_changed': final_values.get('mno_type') != staging.mno_type
                }
            }
        )
        
        self.db.add(structured_activity)
        self.db.flush()  # Get the ID without committing
        
        # Update staging record
        staging.transferred_to_activity_id = structured_activity.id
        staging.transfer_status = 'completed'
        staging.transferred_at = datetime.utcnow()
        staging.approval_status = 'transferred'
        
        # Update email action status
        email_action = self.db.query(EmailAction).filter(EmailAction.id == staging.email_action_id).first()
        if email_action:
            email_action.status = 'completed'
            email_action.executed_at = datetime.utcnow()
            email_action.execution_result = {
                'activity_id': str(structured_activity.id),
                'transfer_type': 'call_log',
                'transferred_at': datetime.utcnow().isoformat()
            }
        
        try:
            self.db.commit()
            print(f"[DEBUG] Successfully committed activity {structured_activity.id} to database")
            
            # Verify the record was created
            verify = self.db.query(SfActivityStructured).filter(
                SfActivityStructured.id == structured_activity.id
            ).first()
            if verify:
                print(f"[DEBUG] Verified activity exists: ID={verify.id}, Subject={verify.subject}")
            else:
                print(f"[ERROR] Activity {structured_activity.id} not found after commit!")
                
        except Exception as e:
            print(f"[ERROR] Failed to commit activity: {e}")
            self.db.rollback()
            raise
        
        return {
            'activity_id': str(structured_activity.id),
            'staging_id': str(staging_id),
            'status': 'completed',
            'message': 'Call log transferred successfully'
        }
    
    def transfer_note_to_persistent(
        self,
        staging_id: UUID,
        user_id: str,
        final_values: Dict[str, Any],
        additional_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Transfer a note from staging to notes table.
        
        Creates a new note record and updates the staging record
        with the transfer status and relationship.
        """
        # Get the staging record
        staging = self.db.query(NoteStaging).filter(NoteStaging.id == staging_id).first()
        if not staging:
            raise ValueError(f"Note staging record {staging_id} not found")
        
        # Check if already transferred
        if staging.transferred_to_note_id:
            raise ValueError(f"Note staging record {staging_id} has already been transferred")
        
        # Create note record using final values from user
        note = Notes(
            user_id=int(user_id) if user_id.isdigit() else 1,  # Convert to int or default
            linked_entity_type=final_values.get('related_entity_type', staging.related_entity_type or 'Contact'),
            linked_entity_id=staging.email_action_id,  # Use email action ID for now
            note_content=final_values.get('note_content', staging.note_content),
            llm_processing_status='Pending',
            # Store original LLM values and user edits for QC
            llm_topics=[{
                'original_llm_content': staging.note_content,
                'user_final_content': final_values.get('note_content', staging.note_content),
                'content_changed': final_values.get('note_content') != staging.note_content,
                'original_entity_type': staging.related_entity_type,
                'final_entity_type': final_values.get('related_entity_type', staging.related_entity_type)
            }]
        )
        
        self.db.add(note)
        self.db.flush()  # Get the ID without committing
        
        # Update staging record
        staging.transferred_to_note_id = note.note_id
        staging.transfer_status = 'completed'
        staging.transferred_at = datetime.utcnow()
        staging.approval_status = 'transferred'
        
        # Update email action status
        email_action = self.db.query(EmailAction).filter(EmailAction.id == staging.email_action_id).first()
        if email_action:
            email_action.status = 'completed'
            email_action.executed_at = datetime.utcnow()
            email_action.execution_result = {
                'note_id': str(note.note_id),
                'transfer_type': 'note',
                'transferred_at': datetime.utcnow().isoformat()
            }
        
        self.db.commit()
        
        return {
            'note_id': note.note_id,
            'staging_id': staging_id,
            'status': 'completed'
        }
    
    def transfer_reminder_to_persistent(
        self,
        staging_id: UUID,
        user_id: str,
        final_values: Dict[str, Any],
        additional_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Transfer a reminder from staging to reminders table.
        
        Creates a new reminder record and updates the staging record
        with the transfer status and relationship.
        """
        # Get the staging record
        staging = self.db.query(ReminderStaging).filter(ReminderStaging.id == staging_id).first()
        if not staging:
            raise ValueError(f"Reminder staging record {staging_id} not found")
        
        # Check if already transferred
        if staging.transferred_to_reminder_id:
            raise ValueError(f"Reminder staging record {staging_id} has already been transferred")
        
        # Create reminder record using final values from user  
        reminder = Reminders(
            user_id=int(user_id) if user_id.isdigit() else 1,  # Convert to int or default
            linked_entity_type=final_values.get('related_entity_type', staging.related_entity_type or 'Contact'),
            linked_entity_id=staging.email_action_id,  # Use email action ID for now
            reminder_type=final_values.get('reminder_type', 'task'),
            description=final_values.get('reminder_text', staging.reminder_text),
            due_date=final_values.get('due_date', staging.due_date),
            is_completed=False
        )
        
        self.db.add(reminder)
        self.db.flush()  # Get the ID without committing
        
        # Update staging record
        staging.transferred_to_reminder_id = reminder.reminder_id
        staging.transfer_status = 'completed'
        staging.transferred_at = datetime.utcnow()
        staging.approval_status = 'transferred'
        
        # Update email action status
        email_action = self.db.query(EmailAction).filter(EmailAction.id == staging.email_action_id).first()
        if email_action:
            email_action.status = 'completed'
            email_action.executed_at = datetime.utcnow()
            email_action.execution_result = {
                'reminder_id': str(reminder.reminder_id),
                'transfer_type': 'reminder',
                'transferred_at': datetime.utcnow().isoformat()
            }
        
        self.db.commit()
        
        return {
            'reminder_id': reminder.reminder_id,
            'staging_id': staging_id,
            'status': 'completed'
        }