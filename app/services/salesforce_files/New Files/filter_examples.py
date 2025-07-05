"""
Example Filter Configurations
Demonstrates how to easily customize data filtering without modifying main analysis code
"""

from data_filters import (
    DataFilterConfig, 
    DataFilter,
    create_recent_months_filter,
    create_recent_days_filter,
    create_date_range_filter
)

def example_basic_analysis():
    """
    Example 1: Basic analysis with minimal filtering
    """
    config = DataFilterConfig()
    config.target_user = None  # Auto-select user with most activities
    config.max_recent_activities = 10
    config.exclude_empty_specialties = True
    
    print("Example 1: Basic Analysis")
    print(f"  - User: Auto-select")
    print(f"  - Activities: {config.max_recent_activities}")
    print(f"  - Exclude empty specialties: {config.exclude_empty_specialties}")
    
    return config

def example_recent_months_filter():
    """
    Example 2: Last 6 months only (reduces dataset size significantly)
    """
    config = create_recent_months_filter(6)
    config.max_recent_activities = 15
    
    print("Example 2: Recent 6 Months Filter")
    print(f"  - Date filter: Last 6 months")
    print(f"  - Activities: {config.max_recent_activities}")
    print(f"  - Benefits: Significantly reduces dataset size")
    
    return config

def example_recent_activity_filter():
    """
    Example 3: Last 90 days for very recent activity analysis
    """
    config = create_recent_days_filter(90)
    config.max_recent_activities = 20
    config.exclude_empty_comments = True
    
    print("Example 3: Recent 90 Days Filter")
    print(f"  - Date filter: Last 90 days")
    print(f"  - Activities: {config.max_recent_activities}")
    print(f"  - Benefits: Focus on very recent outreach trends")
    
    return config

def example_custom_date_range():
    """
    Example 4: Custom date range (e.g., specific quarter or year)
    """
    config = create_date_range_filter('2024-01-01', '2024-12-31')
    config.max_recent_activities = 25
    config.exclude_empty_specialties = True
    
    print("Example 4: Custom Date Range (2024)")
    print(f"  - Date range: 2024-01-01 to 2024-12-31")
    print(f"  - Activities: {config.max_recent_activities}")
    print(f"  - Benefits: Analyze specific time periods")
    
    return config

def example_jennifer_paul_focused():
    """
    Example 5: Focus on Jennifer Paul with comprehensive filtering
    """
    config = DataFilterConfig()
    config.target_user = "Jennifer Paul"
    config.months_back_filter = 6  # Last 6 months
    config.max_recent_activities = 20
    config.exclude_empty_specialties = True
    config.exclude_empty_comments = True
    config.min_comment_length = 15
    
    print("Example 5: Jennifer Paul Focused (6 months)")
    print(f"  - User: {config.target_user}")
    print(f"  - Date filter: Last 6 months")
    print(f"  - Activities: {config.max_recent_activities}")
    print(f"  - Minimum comment length: {config.min_comment_length}")
    
    return config

def example_oncology_specialists():
    """
    Example 6: Focus only on oncology-related outreach (recent months)
    """
    config = DataFilterConfig()
    config.target_user = None
    config.months_back_filter = 4  # Last 4 months
    config.include_only_specialties = [
        "Oncology ? Surgical",
        "Hematology and Medical Oncology",
        "Radiation Oncology",
        "Gynecologic Oncology"
    ]
    config.max_recent_activities = 15
    
    print("Example 6: Oncology Specialists (Last 4 Months)")
    print(f"  - Date filter: Last 4 months")
    print(f"  - Specialties: {config.include_only_specialties}")
    print(f"  - Activities: {config.max_recent_activities}")
    
    return config

def example_direct_visits_only():
    """
    Example 7: Focus only on MD-to-MD visits (recent period)
    """
    config = DataFilterConfig()
    config.target_user = "Sara Murphy"
    config.days_back_filter = 120  # Last 4 months
    config.include_only_outreach_types = ["MD-to-MD Visits"]
    config.max_recent_activities = 25
    config.min_comment_length = 20
    
    print("Example 7: Direct MD-to-MD Visits (Last 120 Days)")
    print(f"  - User: {config.target_user}")
    print(f"  - Date filter: Last 120 days")
    print(f"  - Outreach types: {config.include_only_outreach_types}")
    print(f"  - Activities: {config.max_recent_activities}")
    
    return config

def example_primary_care_focus():
    """
    Example 8: Primary care specialties with quality comments (recent months)
    """
    config = DataFilterConfig()
    config.months_back_filter = 3  # Last 3 months
    config.include_only_specialties = [
        "Internal & Family Medicine",
        "Pediatrics",
        "Geriatrics"
    ]
    config.exclude_empty_comments = True
    config.min_comment_length = 25
    config.max_recent_activities = 15
    
    print("Example 8: Primary Care Focus (Last 3 Months)")
    print(f"  - Date filter: Last 3 months")
    print(f"  - Specialties: {config.include_only_specialties}")
    print(f"  - Minimum comment length: {config.min_comment_length}")
    
    return config

def run_example_analysis():
    """
    Demonstrate how to use different filter configurations
    """
    print("🔧 Filter Configuration Examples")
    print("=" * 50)
    print("\nChoose a filter configuration:")
    
    examples = [
        ("Basic Analysis", example_basic_analysis),
        ("Recent 6 Months Filter", example_recent_months_filter),
        ("Recent 90 Days Filter", example_recent_activity_filter),
        ("Custom Date Range (2024)", example_custom_date_range),
        ("Jennifer Paul Focused (6 months)", example_jennifer_paul_focused),
        ("Oncology Specialists (4 months)", example_oncology_specialists),
        ("Direct MD-to-MD Visits (120 days)", example_direct_visits_only),
        ("Primary Care Focus (3 months)", example_primary_care_focus)
    ]
    
    for i, (name, func) in enumerate(examples, 1):
        print(f"\n{i}. {name}")
        config = func()
        print()
    
    print("\n📅 DATE FILTERING BENEFITS:")
    print("  • Reduces dataset size for faster processing")
    print("  • Focuses on recent trends and patterns")
    print("  • Avoids analysis of outdated outreach data")
    print("  • Improves AI analysis relevance")
    
    print("\n🛠️ TO USE ANY CONFIGURATION:")
    print("1. Copy the configuration code")
    print("2. Paste it into simple_outreach_analyzer.py")
    print("3. Replace the filter_config line with your choice")
    print("\nExample:")
    print("   # Option 2: Last 6 months only")
    print("   filter_config = create_recent_months_filter(6)")

if __name__ == "__main__":
    run_example_analysis() 