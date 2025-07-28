from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from uuid import UUID
from sqlalchemy import select, func, desc, or_
from sqlalchemy.orm import Session

from database.data_models.email_data import Email
# Import EmailParsed to ensure model is loaded for relationships
try:
    from database.data_models.email_parsed_data import EmailParsed
except ImportError:
    pass  # Model might not exist yet


class EmailService:
    """Service for managing emails in the database"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def list_emails(
        self,
        page: int = 1,
        page_size: int = 20,
        search_text: Optional[str] = None,
        from_email: Optional[str] = None,
        processed: Optional[bool] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        sort_by: str = 'date',
        sort_order: str = 'desc'
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        List emails with filtering and pagination
        
        Returns:
            Tuple of (emails list, total count)
        """
        # Base query
        query = self.db.query(Email)
        
        # Apply filters
        if search_text:
            search_pattern = f'%{search_text}%'
            query = query.filter(
                or_(
                    Email.subject.ilike(search_pattern),
                    Email.body.ilike(search_pattern),
                    Email.from_email.ilike(search_pattern)
                )
            )
        
        if from_email:
            query = query.filter(Email.from_email.ilike(f'%{from_email}%'))
        
        if processed is not None:
            query = query.filter(Email.processed == processed)
        
        if start_date:
            # Convert datetime to timestamp for comparison
            start_timestamp = int(start_date.timestamp())
            query = query.filter(Email.date >= start_timestamp)
        
        if end_date:
            # Convert datetime to timestamp for comparison
            end_timestamp = int(end_date.timestamp())
            query = query.filter(Email.date <= end_timestamp)
        
        # Get total count
        total_count = query.count()
        
        # Apply sorting
        if sort_by == 'date':
            sort_column = Email.date
        elif sort_by == 'subject':
            sort_column = Email.subject
        elif sort_by == 'from_email':
            sort_column = Email.from_email
        else:
            sort_column = Email.date
        
        if sort_order == 'desc':
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(sort_column)
        
        # Apply pagination
        offset = (page - 1) * page_size
        emails = query.offset(offset).limit(page_size).all()
        
        # Format results
        results = []
        for email in emails:
            # Convert timestamp to datetime for formatting
            email_date = None
            if email.date:
                email_date = datetime.fromtimestamp(email.date).isoformat()
            
            results.append({
                'id': str(email.id),
                'nylas_id': email.nylas_id,
                'subject': email.subject or 'No subject',
                'snippet': email.snippet,
                'from_email': email.from_email,
                'from_name': email.from_name,
                'to_emails': email.to_emails,
                'date': email_date,
                'unread': email.unread,
                'has_attachments': email.has_attachments,
                'processed': email.processed,
                'processing_status': email.processing_status,
                'classification': email.classification,
                'is_forwarded': email.is_forwarded,
                'user_instruction': email.user_instruction,
                'created_at': email.created_at.isoformat(),
                'body_preview': (email.body[:200] + '...' if email.body and len(email.body) > 200 else email.body)
            })
        
        return results, total_count
    
    def get_email_detail(self, email_id: UUID) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific email"""
        email = self.db.query(Email).filter(Email.id == email_id).first()
        
        if not email:
            return None
        
        # Convert timestamp to datetime for formatting
        email_date = None
        if email.date:
            email_date = datetime.fromtimestamp(email.date).isoformat()
        
        return {
            'id': str(email.id),
            'nylas_id': email.nylas_id,
            'grant_id': email.grant_id,
            'thread_id': email.thread_id,
            'subject': email.subject or 'No subject',
            'snippet': email.snippet,
            'from_email': email.from_email,
            'from_name': email.from_name,
            'to_emails': email.to_emails,
            'cc_emails': email.cc_emails,
            'bcc_emails': email.bcc_emails,
            'date': email_date,
            'body': email.body,
            'body_plain': email.body_plain,
            'unread': email.unread,
            'starred': email.starred,
            'has_attachments': email.has_attachments,
            'attachments_count': email.attachments_count,
            'processed': email.processed,
            'processing_status': email.processing_status,
            'classification': email.classification,
            'is_forwarded': email.is_forwarded,
            'user_instruction': email.user_instruction,
            'extracted_thread': email.extracted_thread,
            'folders': email.folders,
            'labels': email.labels,
            'created_at': email.created_at.isoformat(),
            'updated_at': email.updated_at.isoformat()
        }
    
    def mark_email_processed(self, email_id: UUID, status: str = 'completed') -> bool:
        """Mark an email as processed"""
        email = self.db.query(Email).filter(Email.id == email_id).first()
        
        if not email:
            return False
        
        email.processed = True
        email.processing_status = status
        email.updated_at = datetime.utcnow()
        
        self.db.commit()
        return True
    
    def get_unprocessed_count(self) -> int:
        """Get count of unprocessed emails"""
        return self.db.query(Email).filter(Email.processed == False).count()