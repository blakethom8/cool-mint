"""
Email Sync Manager - Handles both webhook and manual sync modes

This module provides flexible email synchronization with toggle between:
1. Real-time webhook processing (production)
2. Manual/scheduled sync (development)
"""

import os
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from enum import Enum

from sqlalchemy.orm import Session
from nylas import Client

from database.session import db_session
from database.data_models.email_data import Email
from services.nylas_email_service import NylasEmailService
from worker.config import celery_app

logger = logging.getLogger(__name__)


class SyncMode(Enum):
    """Email sync modes"""
    WEBHOOK = "webhook"     # Real-time via webhooks
    MANUAL = "manual"       # On-demand sync
    SCHEDULED = "scheduled" # Periodic sync via cron/celery beat


class EmailSyncManager:
    """Manages email synchronization with configurable modes"""
    
    def __init__(self):
        self.sync_mode = self._get_sync_mode()
        self.client = Client(
            api_key=os.environ.get("NYLAS_API_KEY"),
            api_uri=os.environ.get("NYLAS_API_URI"),
        )
        
    def _get_sync_mode(self) -> SyncMode:
        """Get sync mode from environment or default to manual for development"""
        mode = os.environ.get("EMAIL_SYNC_MODE", "manual").lower()
        try:
            return SyncMode(mode)
        except ValueError:
            logger.warning(f"Invalid sync mode: {mode}, defaulting to manual")
            return SyncMode.MANUAL
    
    def sync_recent_emails(
        self, 
        grant_id: Optional[str] = None,
        minutes_back: int = 30,
        limit: int = 50,
        process_emails: bool = True
    ) -> Dict[str, Any]:
        """
        Sync recent emails from Nylas.
        
        Args:
            grant_id: Nylas grant ID (uses env var if not provided)
            minutes_back: How many minutes back to look for emails
            limit: Maximum number of emails to sync
            process_emails: Whether to queue emails for processing
            
        Returns:
            Dict with sync results
        """
        grant_id = grant_id or os.environ.get("NYLAS_GRANT_ID")
        if not grant_id:
            raise ValueError("No grant_id provided and NYLAS_GRANT_ID not in environment")
        
        # Calculate timestamp for filtering
        since_timestamp = int((datetime.utcnow() - timedelta(minutes=minutes_back)).timestamp())
        
        logger.info(f"Syncing emails from last {minutes_back} minutes (since {since_timestamp})")
        
        results = {
            "total_fetched": 0,
            "new_emails": 0,
            "updated_emails": 0,
            "errors": [],
            "sync_mode": self.sync_mode.value,
            "sync_time": datetime.utcnow().isoformat()
        }
        
        with next(db_session()) as session:
            email_service = NylasEmailService(session)
            
            try:
                # Fetch messages from Nylas with timestamp filter
                query_params = {
                    "limit": limit,
                    "received_after": since_timestamp
                }
                
                messages = self.client.messages.list(grant_id, query_params)
                message_list = messages[0] if isinstance(messages, tuple) else messages
                
                results["total_fetched"] = len(message_list)
                logger.info(f"Fetched {len(message_list)} messages from Nylas")
                
                for message in message_list:
                    try:
                        # Check if email already exists
                        existing_email = session.query(Email).filter_by(
                            nylas_id=message.id
                        ).first()
                        
                        if existing_email:
                            # Update existing email
                            self._update_existing_email(existing_email, message, session)
                            results["updated_emails"] += 1
                        else:
                            # Create new email
                            email = email_service._create_email_from_message(message, grant_id)
                            if email:
                                results["new_emails"] += 1
                                
                                # Queue for processing if enabled
                                if process_emails and not email.processed:
                                    self._queue_email_for_processing(email)
                                    
                    except Exception as e:
                        error_msg = f"Error syncing message {message.id}: {str(e)}"
                        logger.error(error_msg)
                        results["errors"].append(error_msg)
                
                session.commit()
                
            except Exception as e:
                error_msg = f"Error fetching messages from Nylas: {str(e)}"
                logger.error(error_msg)
                results["errors"].append(error_msg)
                session.rollback()
        
        # Log summary
        logger.info(
            f"Sync completed: {results['new_emails']} new, "
            f"{results['updated_emails']} updated, "
            f"{len(results['errors'])} errors"
        )
        
        return results
    
    def _update_existing_email(self, email: Email, message: Any, session: Session):
        """Update existing email with latest data from Nylas"""
        # Update fields that might change
        email.unread = message.unread if hasattr(message, 'unread') else email.unread
        email.starred = message.starred if hasattr(message, 'starred') else email.starred
        email.folders = message.folders if hasattr(message, 'folders') else email.folders
        email.labels = message.labels if hasattr(message, 'labels') else email.labels
        email.updated_at = datetime.utcnow()
        
    def _queue_email_for_processing(self, email: Email):
        """Queue email for AI processing"""
        try:
            task_id = celery_app.send_task(
                "process_email_content",
                args=[str(email.id)],
            )
            logger.info(f"Queued email {email.id} for processing: task {task_id}")
        except Exception as e:
            logger.error(f"Failed to queue email {email.id} for processing: {e}")
    
    def sync_all_unprocessed_emails(self, grant_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Find and process all unprocessed emails in the database.
        
        Returns:
            Dict with processing results
        """
        results = {
            "total_unprocessed": 0,
            "queued_for_processing": 0,
            "errors": []
        }
        
        with next(db_session()) as session:
            # Find all unprocessed emails
            unprocessed_emails = session.query(Email).filter(
                Email.processed == False
            ).all()
            
            results["total_unprocessed"] = len(unprocessed_emails)
            
            for email in unprocessed_emails:
                try:
                    self._queue_email_for_processing(email)
                    results["queued_for_processing"] += 1
                except Exception as e:
                    error_msg = f"Error queueing email {email.id}: {str(e)}"
                    logger.error(error_msg)
                    results["errors"].append(error_msg)
        
        logger.info(
            f"Queued {results['queued_for_processing']} of "
            f"{results['total_unprocessed']} unprocessed emails"
        )
        
        return results
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get current sync status and statistics"""
        with next(db_session()) as session:
            total_emails = session.query(Email).count()
            unprocessed_emails = session.query(Email).filter(
                Email.processed == False
            ).count()
            
            # Get last sync time
            last_email = session.query(Email).order_by(
                Email.created_at.desc()
            ).first()
            
            return {
                "sync_mode": self.sync_mode.value,
                "total_emails": total_emails,
                "unprocessed_emails": unprocessed_emails,
                "last_sync": last_email.created_at.isoformat() if last_email else None,
                "webhook_configured": bool(os.environ.get("WEBHOOK_SECRET")),
                "pinggy_url": os.environ.get("SERVER_URL")
            }