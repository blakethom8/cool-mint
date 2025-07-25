import logging
import os
from typing import List, Optional, Dict, Any
from datetime import datetime

from nylas import Client
from nylas.models.messages import Message
from sqlalchemy.orm import Session

from database.data_models.email_data import Email, EmailAttachment
from database.repository import GenericRepository
from schemas.nylas_email_schema import EmailObject


logger = logging.getLogger(__name__)


class NylasEmailService:
    """Service for syncing emails from Nylas to local database"""
    
    def __init__(self, session: Session):
        self.session = session
        self.client = Client(
            api_key=os.environ.get("NYLAS_API_KEY"),
            api_uri=os.environ.get("NYLAS_API_URI"),
        )
        self.email_repo = GenericRepository(session=session, model=Email)
        self.attachment_repo = GenericRepository(session=session, model=EmailAttachment)
    
    def sync_email_from_webhook(self, webhook_data: Dict[str, Any]) -> Optional[Email]:
        """
        Sync a single email from webhook data to the database.
        
        Args:
            webhook_data: Webhook payload containing email data
            
        Returns:
            Email object if created/updated, None if error
        """
        try:
            # Extract email data from webhook
            email_data = webhook_data.get("object_data", {})
            grant_id = webhook_data.get("grant_id")
            
            if not email_data or not grant_id:
                logger.error("Missing email data or grant_id in webhook")
                return None
            
            # Check if email already exists
            existing_email = self.session.query(Email).filter_by(
                nylas_id=email_data.get("id")
            ).first()
            
            if existing_email:
                logger.info(f"Email {email_data.get('id')} already exists, updating...")
                return self._update_email(existing_email, email_data, webhook_data)
            else:
                logger.info(f"Creating new email {email_data.get('id')}")
                return self._create_email(email_data, grant_id, webhook_data)
                
        except Exception as e:
            logger.error(f"Error syncing email from webhook: {e}")
            return None
    
    def fetch_email_details(self, grant_id: str, message_id: str) -> Optional[Message]:
        """
        Fetch complete email details from Nylas API.
        
        Args:
            grant_id: Nylas grant ID
            message_id: Nylas message ID
            
        Returns:
            Message object from Nylas
        """
        try:
            message = self.client.messages.find(
                identifier=grant_id,
                message_id=message_id
            )
            return message.data if hasattr(message, 'data') else message
        except Exception as e:
            logger.error(f"Error fetching email details: {e}")
            return None
    
    def sync_recent_emails(self, grant_id: str, limit: int = 20) -> List[Email]:
        """
        Sync recent emails from Nylas to database.
        
        Args:
            grant_id: Nylas grant ID
            limit: Number of emails to fetch
            
        Returns:
            List of Email objects
        """
        synced_emails = []
        
        try:
            # Fetch recent messages from Nylas
            messages = self.client.messages.list(grant_id, {"limit": limit})
            message_list = messages[0] if isinstance(messages, tuple) else messages
            
            for message in message_list:
                # Check if email already exists
                existing_email = self.session.query(Email).filter_by(
                    nylas_id=message.id
                ).first()
                
                if not existing_email:
                    email = self._create_email_from_message(message, grant_id)
                    if email:
                        synced_emails.append(email)
                        
            logger.info(f"Synced {len(synced_emails)} new emails")
            return synced_emails
            
        except Exception as e:
            logger.error(f"Error syncing recent emails: {e}")
            return []
    
    def _create_email(self, email_data: Dict[str, Any], grant_id: str, webhook_data: Dict[str, Any]) -> Optional[Email]:
        """Create a new email in the database"""
        try:
            # Extract sender info
            from_list = email_data.get("from", [])
            from_email = from_list[0].get("email") if from_list else None
            from_name = from_list[0].get("name") if from_list else None
            
            # Create email object
            email = Email(
                nylas_id=email_data.get("id"),
                grant_id=grant_id,
                thread_id=email_data.get("thread_id"),
                subject=email_data.get("subject"),
                snippet=email_data.get("snippet"),
                date=email_data.get("date"),
                from_email=from_email,
                from_name=from_name,
                to_emails=[p.get("email") for p in email_data.get("to", [])],
                cc_emails=[p.get("email") for p in email_data.get("cc", [])],
                bcc_emails=[p.get("email") for p in email_data.get("bcc", [])],
                body=email_data.get("body"),
                unread=email_data.get("unread", True),
                starred=email_data.get("starred", False),
                folders=email_data.get("folders", []),
                labels=email_data.get("labels", []),
                has_attachments=bool(email_data.get("attachments")),
                attachments_count=len(email_data.get("attachments", [])),
                raw_webhook_data=webhook_data,
                processed=False,
                processing_status="pending"
            )
            
            self.email_repo.create(obj=email)
            
            # Create attachments if any
            if email_data.get("attachments"):
                self._create_attachments(email, email_data.get("attachments", []), grant_id)
            
            return email
            
        except Exception as e:
            logger.error(f"Error creating email: {e}")
            self.session.rollback()
            return None
    
    def _create_email_from_message(self, message: Message, grant_id: str) -> Optional[Email]:
        """Create email from Nylas Message object"""
        try:
            # Extract sender info
            from_email = None
            from_name = None
            if message.from_ and len(message.from_) > 0:
                sender = message.from_[0]
                if isinstance(sender, dict):
                    from_email = sender.get("email")
                    from_name = sender.get("name")
                else:
                    from_email = getattr(sender, "email", None)
                    from_name = getattr(sender, "name", None)
            
            # Create email object
            email = Email(
                nylas_id=message.id,
                grant_id=grant_id,
                thread_id=message.thread_id,
                subject=message.subject,
                snippet=message.snippet,
                date=message.date,
                from_email=from_email,
                from_name=from_name,
                to_emails=self._extract_emails(message.to),
                cc_emails=self._extract_emails(message.cc),
                bcc_emails=self._extract_emails(message.bcc),
                body=message.body,
                unread=message.unread,
                starred=message.starred,
                folders=message.folders if hasattr(message, 'folders') else [],
                labels=message.labels if hasattr(message, 'labels') else [],
                has_attachments=bool(message.attachments) if hasattr(message, 'attachments') else False,
                attachments_count=len(message.attachments) if hasattr(message, 'attachments') else 0,
                processed=False,
                processing_status="pending"
            )
            
            self.email_repo.create(obj=email)
            
            # Create attachments if any
            if hasattr(message, 'attachments') and message.attachments:
                self._create_attachments_from_message(email, message.attachments, grant_id)
            
            return email
            
        except Exception as e:
            logger.error(f"Error creating email from message: {e}")
            self.session.rollback()
            return None
    
    def _update_email(self, email: Email, email_data: Dict[str, Any], webhook_data: Dict[str, Any]) -> Email:
        """Update existing email with new data"""
        try:
            # Update email fields
            email.unread = email_data.get("unread", email.unread)
            email.starred = email_data.get("starred", email.starred)
            email.folders = email_data.get("folders", email.folders)
            email.labels = email_data.get("labels", email.labels)
            email.raw_webhook_data = webhook_data
            email.updated_at = datetime.utcnow()
            
            self.email_repo.update(obj=email)
            return email
            
        except Exception as e:
            logger.error(f"Error updating email: {e}")
            self.session.rollback()
            return None
    
    def _create_attachments(self, email: Email, attachments: List[Dict[str, Any]], grant_id: str):
        """Create attachment records for an email"""
        for att_data in attachments:
            try:
                attachment = EmailAttachment(
                    email_id=email.id,
                    nylas_id=att_data.get("id"),
                    grant_id=grant_id,
                    filename=att_data.get("filename", "unknown"),
                    content_type=att_data.get("content_type", "application/octet-stream"),
                    size=att_data.get("size", 0),
                    content_id=att_data.get("content_id"),
                    content_disposition=att_data.get("content_disposition"),
                    is_inline=att_data.get("is_inline", False),
                    downloaded=False
                )
                self.attachment_repo.create(obj=attachment)
            except Exception as e:
                logger.error(f"Error creating attachment: {e}")
    
    def _create_attachments_from_message(self, email: Email, attachments: List[Any], grant_id: str):
        """Create attachment records from Message attachments"""
        for att in attachments:
            try:
                attachment = EmailAttachment(
                    email_id=email.id,
                    nylas_id=att.id if hasattr(att, 'id') else att.get('id'),
                    grant_id=grant_id,
                    filename=att.filename if hasattr(att, 'filename') else att.get('filename', 'unknown'),
                    content_type=att.content_type if hasattr(att, 'content_type') else att.get('content_type', 'application/octet-stream'),
                    size=att.size if hasattr(att, 'size') else att.get('size', 0),
                    content_id=att.content_id if hasattr(att, 'content_id') else att.get('content_id'),
                    content_disposition=att.content_disposition if hasattr(att, 'content_disposition') else att.get('content_disposition'),
                    is_inline=att.is_inline if hasattr(att, 'is_inline') else att.get('is_inline', False),
                    downloaded=False
                )
                self.attachment_repo.create(obj=attachment)
            except Exception as e:
                logger.error(f"Error creating attachment from message: {e}")
    
    def _extract_emails(self, participants: Optional[List[Any]]) -> List[str]:
        """Extract email addresses from participant list"""
        if not participants:
            return []
        
        emails = []
        for p in participants:
            if isinstance(p, dict):
                email = p.get("email")
            else:
                email = getattr(p, "email", None)
            if email:
                emails.append(email)
        return emails