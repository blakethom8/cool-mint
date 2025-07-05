"""
Data Filtering and Preparation Configuration
Handles all data filtering, selection, and preparation logic separate from AI analysis
"""

from typing import Dict, List, Optional, Any
import pandas as pd
from datetime import datetime, timedelta

class DataFilterConfig:
    """Configuration class for data filtering and preparation"""
    
    def __init__(self):
        # User selection criteria
        self.target_user = None  # None = auto-select user with most activities
        self.max_recent_activities = 15  # Number of recent activities to analyze
        
        # Column mapping and selection
        self.required_columns = [
            'Assigned',
            'MN Specialty Group', 
            'FullName',
            'Date',
            'Outreach Type',
            'Subject',
            'Full Comments'
        ]
        
        # Date filtering criteria - NEW FUNCTIONALITY
        self.date_range_filter = None  # Format: {'start': 'YYYY-MM-DD', 'end': 'YYYY-MM-DD'}
        self.days_back_filter = 30   # Filter to last N days (e.g., 90 for last 3 months)
        self.months_back_filter = None  # Filter to last N months (e.g., 6 for last 6 months)
        
        # Activity filtering criteria
        self.exclude_empty_specialties = True
        self.exclude_empty_comments = False
        
        # Specialty group filters
        self.exclude_specialties = ['']  # Empty specialty groups to exclude
        self.include_only_specialties = None  # None = include all, or list of specific specialties
        
        # Outreach type filters
        self.exclude_outreach_types = []  # Outreach types to exclude
        self.include_only_outreach_types = None  # None = include all
        
        # Comment length preferences
        self.max_comment_length = 200  # Truncate comments longer than this
        self.min_comment_length = 0    # Exclude comments shorter than this

class DataFilter:
    """Main data filtering and preparation class"""
    
    def __init__(self, config: DataFilterConfig = None):
        self.config = config or DataFilterConfig()
    
    def parse_date_column(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Parse and standardize the Date column for filtering
        """
        if 'Date' not in df.columns:
            print("Warning: 'Date' column not found in data")
            return df
        
        # Convert Date column to datetime
        try:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            # Remove rows with invalid dates
            initial_count = len(df)
            df = df.dropna(subset=['Date'])
            if len(df) < initial_count:
                print(f"Removed {initial_count - len(df)} records with invalid dates")
            
        except Exception as e:
            print(f"Warning: Could not parse dates: {str(e)}")
        
        return df
    
    def apply_date_filters(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply date-based filtering - NEW FUNCTIONALITY
        """
        if 'Date' not in df.columns:
            return df
        
        initial_count = len(df)
        
        # Apply days back filter
        if self.config.days_back_filter:
            cutoff_date = datetime.now() - timedelta(days=self.config.days_back_filter)
            df = df[df['Date'] >= cutoff_date]
            print(f"Applied {self.config.days_back_filter}-day filter: {initial_count} → {len(df)} records")
        
        # Apply months back filter
        elif self.config.months_back_filter:
            cutoff_date = datetime.now() - timedelta(days=self.config.months_back_filter * 30)
            df = df[df['Date'] >= cutoff_date]
            print(f"Applied {self.config.months_back_filter}-month filter: {initial_count} → {len(df)} records")
        
        # Apply specific date range filter
        elif self.config.date_range_filter:
            start_date = pd.to_datetime(self.config.date_range_filter['start'])
            end_date = pd.to_datetime(self.config.date_range_filter['end'])
            df = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)]
            print(f"Applied date range filter ({self.config.date_range_filter['start']} to {self.config.date_range_filter['end']}): {initial_count} → {len(df)} records")
        
        return df
    
    def select_target_user(self, df: pd.DataFrame, assigned_counts: pd.Series) -> Optional[str]:
        """
        Select the target user based on configuration
        """
        if self.config.target_user:
            if self.config.target_user in assigned_counts.index:
                print(f"Using specified user: {self.config.target_user}")
                return self.config.target_user
            else:
                print(f"Warning: Specified user '{self.config.target_user}' not found.")
                print("Available users:")
                for user in assigned_counts.index:
                    print(f"  - {user} ({assigned_counts[user]} activities)")
                return None
        else:
            # Auto-select user with most activities
            target_user = assigned_counts.index[0]
            print(f"Auto-selected user with most activities: {target_user}")
            return target_user
    
    def filter_user_data(self, df: pd.DataFrame, assigned_user: str) -> pd.DataFrame:
        """
        Filter dataframe for a specific assigned user
        """
        if 'Assigned' not in df.columns:
            raise ValueError("'Assigned' column not found in data")
        
        filtered_df = df[df['Assigned'] == assigned_user].copy()
        print(f"Filtered data for '{assigned_user}': {len(filtered_df)} records")
        
        return filtered_df
    
    def apply_specialty_filters(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply specialty-based filtering
        """
        initial_count = len(df)
        
        # Exclude empty specialties if configured
        if self.config.exclude_empty_specialties and 'MN Specialty Group' in df.columns:
            df = df[~df['MN Specialty Group'].isin(self.config.exclude_specialties)]
        
        # Include only specific specialties if configured
        if self.config.include_only_specialties and 'MN Specialty Group' in df.columns:
            df = df[df['MN Specialty Group'].isin(self.config.include_only_specialties)]
        
        filtered_count = len(df)
        if filtered_count != initial_count:
            print(f"Specialty filtering: {initial_count} → {filtered_count} records")
        
        return df
    
    def apply_outreach_type_filters(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply outreach type filtering
        """
        initial_count = len(df)
        
        # Exclude specific outreach types
        if self.config.exclude_outreach_types and 'Outreach Type' in df.columns:
            df = df[~df['Outreach Type'].isin(self.config.exclude_outreach_types)]
        
        # Include only specific outreach types if configured
        if self.config.include_only_outreach_types and 'Outreach Type' in df.columns:
            df = df[df['Outreach Type'].isin(self.config.include_only_outreach_types)]
        
        filtered_count = len(df)
        if filtered_count != initial_count:
            print(f"Outreach type filtering: {initial_count} → {filtered_count} records")
        
        return df
    
    def apply_comment_filters(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply comment-based filtering
        """
        initial_count = len(df)
        
        if 'Full Comments' in df.columns:
            # Exclude empty comments if configured
            if self.config.exclude_empty_comments:
                df = df[df['Full Comments'].notna() & (df['Full Comments'].str.len() > 0)]
            
            # Apply minimum comment length filter
            if self.config.min_comment_length > 0:
                df = df[df['Full Comments'].str.len() >= self.config.min_comment_length]
        
        filtered_count = len(df)
        if filtered_count != initial_count:
            print(f"Comment filtering: {initial_count} → {filtered_count} records")
        
        return df
    
    def select_recent_activities(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Select the most recent activities based on configuration
        """
        if len(df) <= self.config.max_recent_activities:
            print(f"Using all {len(df)} available activities")
            return df
        else:
            # Sort by date to get truly recent activities
            if 'Date' in df.columns:
                df_sorted = df.sort_values('Date', ascending=False)
                recent_df = df_sorted.head(self.config.max_recent_activities)
            else:
                recent_df = df.tail(self.config.max_recent_activities)
            
            print(f"Selected {len(recent_df)} most recent activities from {len(df)} total")
            return recent_df
    
    def prepare_activity_data(self, row: pd.Series) -> Dict[str, Any]:
        """
        Prepare a single activity record for LLM analysis
        """
        # Get comment and apply length truncation
        comments = str(row.get('Full Comments', 'N/A'))
        if len(comments) > self.config.max_comment_length:
            comments = comments[:self.config.max_comment_length] + "..."
        
        # Format date properly
        date_value = row.get('Date', 'N/A')
        if pd.notna(date_value) and hasattr(date_value, 'strftime'):
            date_str = date_value.strftime('%Y-%m-%d')
        else:
            date_str = str(date_value)
        
        activity = {
            "date": date_str,
            "specialty_group": row.get('MN Specialty Group', 'N/A'),
            "physician_name": row.get('FullName', 'N/A'),
            "outreach_type": row.get('Outreach Type', 'N/A'),
            "subject": row.get('Subject', 'N/A'),
            "comments": comments
        }
        
        return activity
    
    def prepare_for_llm_analysis(self, df: pd.DataFrame, assigned_user: str) -> Optional[Dict[str, Any]]:
        """
        Complete data preparation pipeline for LLM analysis
        """
        print(f"\n=== DATA FILTERING PIPELINE FOR {assigned_user.upper()} ===")
        
        try:
            # Step 0: Parse dates for filtering
            df = self.parse_date_column(df)
            
            # Step 1: Filter by user
            filtered_df = self.filter_user_data(df, assigned_user)
            
            if len(filtered_df) == 0:
                print("No data found after user filtering")
                return None
            
            # Step 2: Apply date filters - NEW STEP
            filtered_df = self.apply_date_filters(filtered_df)
            
            if len(filtered_df) == 0:
                print("No data remaining after date filtering")
                return None
            
            # Step 3: Apply specialty filters
            filtered_df = self.apply_specialty_filters(filtered_df)
            
            # Step 4: Apply outreach type filters  
            filtered_df = self.apply_outreach_type_filters(filtered_df)
            
            # Step 5: Apply comment filters
            filtered_df = self.apply_comment_filters(filtered_df)
            
            if len(filtered_df) == 0:
                print("No data remaining after applying filters")
                return None
            
            # Step 6: Select recent activities
            recent_df = self.select_recent_activities(filtered_df)
            
            # Step 7: Prepare final data structure
            llm_data = {
                "assigned_user": assigned_user,
                "total_activities": len(filtered_df),
                "recent_activities": []
            }
            
            for _, row in recent_df.iterrows():
                activity = self.prepare_activity_data(row)
                llm_data["recent_activities"].append(activity)
            
            print(f"Final prepared data: {len(llm_data['recent_activities'])} activities for analysis")
            return llm_data
            
        except Exception as e:
            print(f"Error in data preparation pipeline: {str(e)}")
            return None

# Pre-configured filter setups for common use cases

def create_basic_filter() -> DataFilterConfig:
    """Basic filtering configuration - minimal filters"""
    config = DataFilterConfig()
    config.max_recent_activities = 10
    config.exclude_empty_specialties = True
    return config

def create_recent_months_filter(months: int = 6) -> DataFilterConfig:
    """Filter for recent months to reduce dataset size"""
    config = DataFilterConfig()
    config.months_back_filter = months
    config.max_recent_activities = 15
    config.exclude_empty_specialties = True
    print(f"Created filter for last {months} months")
    return config

def create_recent_days_filter(days: int = 90) -> DataFilterConfig:
    """Filter for recent days to reduce dataset size"""
    config = DataFilterConfig()
    config.days_back_filter = days
    config.max_recent_activities = 15
    config.exclude_empty_specialties = True
    print(f"Created filter for last {days} days")
    return config

def create_date_range_filter(start_date: str, end_date: str) -> DataFilterConfig:
    """Filter for specific date range"""
    config = DataFilterConfig()
    config.date_range_filter = {'start': start_date, 'end': end_date}
    config.max_recent_activities = 20
    config.exclude_empty_specialties = True
    print(f"Created date range filter: {start_date} to {end_date}")
    return config

def create_comprehensive_filter() -> DataFilterConfig:
    """Comprehensive filtering - more detailed analysis"""
    config = DataFilterConfig()
    config.max_recent_activities = 20
    config.exclude_empty_specialties = True
    config.exclude_empty_comments = True
    config.min_comment_length = 10
    return config

def create_specialty_focused_filter(target_specialties: List[str]) -> DataFilterConfig:
    """Filter focused on specific medical specialties"""
    config = DataFilterConfig()
    config.include_only_specialties = target_specialties
    config.max_recent_activities = 15
    config.exclude_empty_specialties = True
    return config

def create_outreach_type_filter(target_outreach_types: List[str]) -> DataFilterConfig:
    """Filter focused on specific outreach types"""
    config = DataFilterConfig()
    config.include_only_outreach_types = target_outreach_types
    config.max_recent_activities = 15
    return config 