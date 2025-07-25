"""
Email Sync Configuration

This module manages the configuration for email synchronization,
allowing easy switching between webhook and manual sync modes.
"""

import os
from enum import Enum
from typing import Optional, Dict, Any


class EmailSyncConfig:
    """Email sync configuration manager"""
    
    # Default configuration
    DEFAULT_CONFIG = {
        "sync_mode": "manual",  # webhook, manual, or scheduled
        "sync_interval_minutes": 5,  # For scheduled mode
        "sync_lookback_minutes": 30,  # How far back to look for emails
        "batch_size": 50,  # Max emails per sync
        "process_on_sync": True,  # Queue emails for AI processing
        "webhook_port": 8080,  # Local port for webhook server
        "auto_cleanup_webhooks": True,  # Cleanup webhooks on shutdown
    }
    
    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        """Get current configuration from environment and defaults"""
        config = cls.DEFAULT_CONFIG.copy()
        
        # Override with environment variables if present
        if os.environ.get("EMAIL_SYNC_MODE"):
            config["sync_mode"] = os.environ.get("EMAIL_SYNC_MODE")
        
        if os.environ.get("EMAIL_SYNC_INTERVAL"):
            config["sync_interval_minutes"] = int(os.environ.get("EMAIL_SYNC_INTERVAL"))
        
        if os.environ.get("EMAIL_SYNC_LOOKBACK"):
            config["sync_lookback_minutes"] = int(os.environ.get("EMAIL_SYNC_LOOKBACK"))
        
        if os.environ.get("EMAIL_BATCH_SIZE"):
            config["batch_size"] = int(os.environ.get("EMAIL_BATCH_SIZE"))
        
        if os.environ.get("EMAIL_PROCESS_ON_SYNC"):
            config["process_on_sync"] = os.environ.get("EMAIL_PROCESS_ON_SYNC").lower() == "true"
        
        return config
    
    @classmethod
    def set_sync_mode(cls, mode: str):
        """Set sync mode in environment"""
        valid_modes = ["webhook", "manual", "scheduled"]
        if mode not in valid_modes:
            raise ValueError(f"Invalid sync mode: {mode}. Must be one of {valid_modes}")
        
        os.environ["EMAIL_SYNC_MODE"] = mode
        
        # Also update .env file if it exists
        env_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
            '.env'
        )
        if os.path.exists(env_path):
            from dotenv import set_key
            set_key(env_path, "EMAIL_SYNC_MODE", mode)
    
    @classmethod
    def is_webhook_mode(cls) -> bool:
        """Check if currently in webhook mode"""
        config = cls.get_config()
        return config["sync_mode"] == "webhook"
    
    @classmethod
    def is_manual_mode(cls) -> bool:
        """Check if currently in manual mode"""
        config = cls.get_config()
        return config["sync_mode"] == "manual"
    
    @classmethod
    def is_scheduled_mode(cls) -> bool:
        """Check if currently in scheduled mode"""
        config = cls.get_config()
        return config["sync_mode"] == "scheduled"
    
    @classmethod
    def get_status(cls) -> Dict[str, Any]:
        """Get comprehensive sync status"""
        config = cls.get_config()
        
        status = {
            "config": config,
            "environment": {
                "nylas_configured": bool(os.environ.get("NYLAS_API_KEY")),
                "grant_id_configured": bool(os.environ.get("NYLAS_GRANT_ID")),
                "webhook_secret_configured": bool(os.environ.get("WEBHOOK_SECRET")),
                "server_url_configured": bool(os.environ.get("SERVER_URL")),
            }
        }
        
        # Add mode-specific status
        if config["sync_mode"] == "webhook":
            status["webhook_ready"] = (
                status["environment"]["webhook_secret_configured"] and
                status["environment"]["server_url_configured"]
            )
        
        return status