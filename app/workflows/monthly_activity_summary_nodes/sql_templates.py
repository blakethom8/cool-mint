"""
SQL Templates for Monthly Activity Summary Workflow

This module contains SQL query templates for retrieving activity data
from the Salesforce database tables.
"""

from typing import Dict, Any, List
from datetime import datetime, date


class MonthlyActivitySQLTemplates:
    """SQL query templates for monthly activity summary operations."""

    @staticmethod
    def get_monthly_activities_query() -> str:
        """
        Get all activities for a user within a date range with contact and user information.

        Returns:
            SQL query string with placeholders for user_id, start_date, and end_date
        """
        return """
        SELECT 
            a.id as activity_id,
            a.salesforce_id as activity_sf_id,
            a.subject,
            a.description,
            a.activity_date,
            a.status,
            a.priority,
            a.type as activity_type,
            a.mno_type,
            a.mno_subtype,
            a.mn_tags,
            a.comments_short,
            a.sf_created_date,
            a.sf_last_modified_date,
            
            -- Contact information
            c.id as contact_id,
            c.salesforce_id as contact_sf_id,
            c.name as contact_name,
            c.first_name as contact_first_name,
            c.last_name as contact_last_name,
            c.email as contact_email,
            c.phone as contact_phone,
            c.title as contact_title,
            c.specialty,
            c.primary_mgma_specialty,
            c.specialty_group,
            c.sub_specialty,
            c.contact_account_name,
            c.primary_practice_location_id,
            c.geography,
            c.primary_geography,
            c.is_physician,
            c.provider_type,
            c.network_picklist,
            c.sub_network,
            
            -- NEW: Additional contact fields requested by user
            c.mailing_city,
            c.employment_status_mn as employment_status,
            c.mn_mgma_specialty,
            c.mn_primary_geography,
            c.mn_specialty_group,
            
            -- User information
            u.id as user_id,
            u.salesforce_id as user_sf_id,
            u.name as user_name,
            u.first_name as user_first_name,
            u.last_name as user_last_name,
            u.email as user_email
            
        FROM sf_activities a
        LEFT JOIN sf_contacts c ON a.contact_id = c.id
        LEFT JOIN sf_users u ON a.owner_id = u.salesforce_id
        WHERE a.owner_id = :user_id
          AND a.activity_date >= :start_date
          AND a.activity_date <= :end_date
          AND a.description IS NOT NULL
          AND a.description != ''
          AND a.is_deleted = false
        ORDER BY a.activity_date DESC, a.sf_created_date DESC
        """

    @staticmethod
    def get_individual_activities_query() -> str:
        """
        Get individual activities with complete contact context (simplified version).

        This is the new primary query focusing on individual activity details
        rather than aggregated statistics.

        Returns:
            SQL query string with comprehensive activity and contact information
        """
        return """
        SELECT 
            -- Core activity information
            a.activity_date,
            a.mno_type,
            a.mno_subtype,
            a.description,
            a.subject,
            a.status,
            a.priority,
            a.type as activity_type,
            a.mn_tags,
            a.comments_short,
            
            -- Contact information (complete provider context)
            c.name as contact_name,
            c.mailing_city,
            c.specialty,
            c.contact_account_name,
            c.employment_status_mn as employment_status,
            c.mn_mgma_specialty,
            c.mn_primary_geography,
            c.mn_specialty_group,
            c.title as contact_title,
            c.is_physician,
            c.provider_type,
            c.email as contact_email,
            c.phone as contact_phone
            
        FROM sf_activities a
        LEFT JOIN sf_contacts c ON a.contact_id = c.id
        WHERE a.owner_id = :user_id
          AND a.activity_date >= :start_date
          AND a.activity_date <= :end_date
          AND a.description IS NOT NULL
          AND a.description != ''
          AND a.is_deleted = false
        ORDER BY a.activity_date DESC, a.sf_created_date DESC
        """

    @staticmethod
    def get_activity_summary_stats_query() -> str:
        """
        Get summary statistics for activities within a date range.

        Returns:
            SQL query string for activity statistics
        """
        return """
        SELECT 
            COUNT(*) as total_activities,
            COUNT(DISTINCT a.contact_id) as unique_contacts,
            COUNT(DISTINCT c.specialty) as unique_specialties,
            COUNT(DISTINCT c.contact_account_name) as unique_organizations,
            COUNT(DISTINCT DATE(a.activity_date)) as active_days,
            MIN(a.activity_date) as earliest_activity,
            MAX(a.activity_date) as latest_activity,
            
            -- Activity type breakdown
            COUNT(CASE WHEN a.type = 'Task' THEN 1 END) as task_count,
            COUNT(CASE WHEN a.type = 'Event' THEN 1 END) as event_count,
            
            -- Priority breakdown
            COUNT(CASE WHEN a.priority = 'High' THEN 1 END) as high_priority_count,
            COUNT(CASE WHEN a.priority = 'Normal' THEN 1 END) as normal_priority_count,
            COUNT(CASE WHEN a.priority = 'Low' THEN 1 END) as low_priority_count,
            
            -- Status breakdown
            COUNT(CASE WHEN a.is_closed = true THEN 1 END) as closed_activities,
            COUNT(CASE WHEN a.is_closed = false THEN 1 END) as open_activities
            
        FROM sf_activities a
        LEFT JOIN sf_contacts c ON a.contact_id = c.id
        WHERE a.owner_id = :user_id
          AND a.activity_date >= :start_date
          AND a.activity_date <= :end_date
          AND a.description IS NOT NULL
          AND a.description != ''
          AND a.is_deleted = false
        """

    @staticmethod
    def get_specialty_breakdown_query() -> str:
        """
        Get activity breakdown by specialty.

        Returns:
            SQL query string for specialty analysis
        """
        return """
        SELECT 
            COALESCE(c.specialty, 'Unknown') as specialty,
            COUNT(*) as activity_count,
            COUNT(DISTINCT a.contact_id) as unique_contacts,
            COUNT(DISTINCT c.contact_account_name) as unique_organizations,
            
            -- Recent activity indicators
            COUNT(CASE WHEN a.activity_date >= CURRENT_DATE - INTERVAL '7 days' THEN 1 END) as recent_activities,
            MAX(a.activity_date) as last_activity_date,
            
            -- Priority distribution
            COUNT(CASE WHEN a.priority = 'High' THEN 1 END) as high_priority_count,
            
            -- Sample contact names (for context)
            STRING_AGG(DISTINCT c.name, ', ') FILTER (WHERE c.name IS NOT NULL) as sample_contacts
            
        FROM sf_activities a
        LEFT JOIN sf_contacts c ON a.contact_id = c.id
        WHERE a.owner_id = :user_id
          AND a.activity_date >= :start_date
          AND a.activity_date <= :end_date
          AND a.description IS NOT NULL
          AND a.description != ''
          AND a.is_deleted = false
        GROUP BY COALESCE(c.specialty, 'Unknown')
        ORDER BY activity_count DESC
        """

    @staticmethod
    def get_contact_activity_summary_query() -> str:
        """
        Get activity summary grouped by contact.

        Returns:
            SQL query string for contact-based activity analysis
        """
        return """
        SELECT 
            c.id as contact_id,
            c.name as contact_name,
            c.specialty,
            c.contact_account_name,
            c.title,
            c.geography,
            c.is_physician,
            
            COUNT(*) as total_activities,
            MAX(a.activity_date) as last_activity_date,
            MIN(a.activity_date) as first_activity_date,
            
            -- Activity type breakdown
            COUNT(CASE WHEN a.type = 'Task' THEN 1 END) as task_count,
            COUNT(CASE WHEN a.type = 'Event' THEN 1 END) as event_count,
            
            -- Priority breakdown
            COUNT(CASE WHEN a.priority = 'High' THEN 1 END) as high_priority_count,
            
            -- Recent activity
            COUNT(CASE WHEN a.activity_date >= CURRENT_DATE - INTERVAL '7 days' THEN 1 END) as recent_activities,
            
            -- Sample subjects (for context)
            STRING_AGG(DISTINCT a.subject, ' | ') FILTER (WHERE a.subject IS NOT NULL) as sample_subjects
            
        FROM sf_activities a
        LEFT JOIN sf_contacts c ON a.contact_id = c.id
        WHERE a.owner_id = :user_id
          AND a.activity_date >= :start_date
          AND a.activity_date <= :end_date
          AND a.description IS NOT NULL
          AND a.description != ''
          AND a.is_deleted = false
          AND c.id IS NOT NULL
        GROUP BY c.id, c.name, c.specialty, c.contact_account_name, c.title, c.geography, c.is_physician
        ORDER BY total_activities DESC, last_activity_date DESC
        """
