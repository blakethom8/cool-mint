"""
Targeted Contact Sync Package

This package provides targeted contact synchronization functionality,
focusing on syncing only contacts that have activities logged against them.
"""

from .rest_salesforce_service import RestSalesforceService
from .targeted_contact_sync_service import TargetedContactSyncService

__all__ = ["RestSalesforceService", "TargetedContactSyncService"]
