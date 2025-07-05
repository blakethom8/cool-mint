"""
Simplified Healthcare Outreach Analyzer
Clean separation of concerns - focuses purely on AI analysis
"""

import os
import json
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from pydantic_ai import Agent
from excel_processor import process_html_excel_file
from data_filters import (
    DataFilter, 
    DataFilterConfig, 
    create_basic_filter, 
    create_comprehensive_filter,
    create_recent_months_filter,
    create_recent_days_filter,
    create_date_range_filter
)
from config import setup_openai_key

# Set up OpenAI API key from environment
from dotenv import load_dotenv
load_dotenv()

# Simplified model to avoid validation issues
class SpecialtyAnalysis(BaseModel):
    """Simplified model for specialty targeting analysis results"""
    assigned_user: str
    total_activities: int
    top_specialties: List[str]  # Simplified to just list of strings
    outreach_patterns: List[str]
    key_insights: List[str]
    specialty_focus_summary: str

def create_outreach_agent() -> Optional[Agent]:
    """
    Create the AI agent after ensuring API key is available
    """
    try:
        agent = Agent(
            model='openai:gpt-4o-mini',
            result_type=SpecialtyAnalysis,
            system_prompt="""You are a healthcare business development analyst. 
            
            Analyze outreach specialist data to understand specialty targeting patterns.
            
            Focus on:
            - Top medical specialties being targeted (return as simple list of specialty names)
            - Outreach strategies and patterns 
            - Key insights about their approach
            - Summary of their specialty focus strategy
            
            Keep responses concise and actionable. Return specialty names as simple strings in a list."""
        )
        return agent
    except Exception as e:
        print(f"❌ Failed to create AI agent: {str(e)}")
        print("   Make sure your OPENAI_API_KEY is set correctly")
        return None

def analyze_with_ai(outreach_data: dict, agent: Agent) -> Optional[SpecialtyAnalysis]:
    """
    Simple AI analysis function - focused purely on LLM interaction
    """
    print(f"🤖 Running AI analysis for {outreach_data['assigned_user']}...")
    
    # Build simple prompt
    prompt = f"""
    Healthcare Outreach Specialist: {outreach_data['assigned_user']}
    Total Activities: {outreach_data['total_activities']}
    
    Recent Activities:
    """
    
    for i, activity in enumerate(outreach_data['recent_activities']):
        prompt += f"""
    {i+1}. {activity['date']} - {activity['specialty_group']}
       Physician: {activity['physician_name']}
       Type: {activity['outreach_type']}
       Subject: {activity['subject']}
       Notes: {activity['comments'][:150]}...
    """
    
    prompt += """
    
    Please analyze this outreach data and provide:
    1. top_specialties: List the top 5-7 medical specialties this person targets most
    2. outreach_patterns: List 3-5 key patterns in their outreach approach
    3. key_insights: List 3-5 important insights about their strategy
    4. specialty_focus_summary: Write a 2-3 sentence summary of their specialty focus
    
    Keep all responses concise and professional.
    """
    
    try:
        result = agent.run_sync(prompt)
        return result.data
    except Exception as e:
        print(f"❌ AI analysis failed: {str(e)}")
        print("   This could be a temporary API issue. Try running again.")
        return None

def print_analysis_report(analysis: SpecialtyAnalysis):
    """
    Simple, clean report display
    """
    print(f"\n{'='*60}")
    print(f"🏥 ANALYSIS REPORT: {analysis.assigned_user}")
    print(f"{'='*60}")
    
    print(f"\n📊 Total Activities: {analysis.total_activities}")
    
    print(f"\n🎯 Top Specialties:")
    for specialty in analysis.top_specialties:
        print(f"   • {specialty}")
    
    print(f"\n📋 Outreach Patterns:")
    for pattern in analysis.outreach_patterns:
        print(f"   • {pattern}")
    
    print(f"\n💡 Key Insights:")
    for insight in analysis.key_insights:
        print(f"   • {insight}")
    
    print(f"\n📝 Summary:")
    print(f"   {analysis.specialty_focus_summary}")
    
    print(f"\n{'='*60}")

def main():
    """
    Main analysis function - simple and focused
    """
    print("🏥 Simple Healthcare Outreach Analysis")
    print("=" * 50)
    
    # Check API key
    if not setup_openai_key():
        return
    
    # Create AI agent after API key is confirmed
    print("\n🤖 Setting up AI agent...")
    agent = create_outreach_agent()
    if not agent:
        return
    
    # Load data
    print("\n📂 Loading data...")
    df, headers, assigned_counts = process_html_excel_file("report1749182913520.xls")
    
    if df is None:
        print("❌ Failed to load data")
        return
    
    # Configure filters - WITH NEW DATE FILTERING OPTIONS
    print("\n⚙️ Setting up filters...")
    
    # CHOOSE ONE OF THESE FILTER OPTIONS:
    
    # Option 1: Basic filter (no date filtering)
    # filter_config = create_basic_filter()
    
    # Option 2: Last 6 months only (reduces dataset size significantly)
    filter_config = create_recent_months_filter(6)
    
    # Option 3: Last 90 days only (for very recent activity)
    # filter_config = create_recent_days_filter(90)
    
    # Option 4: Custom date range
    # filter_config = create_date_range_filter('2024-01-01', '2024-12-31')
    
    # Option 5: Comprehensive with date filtering
    # filter_config = create_comprehensive_filter()
    # filter_config.months_back_filter = 3  # Last 3 months
    
    # Uncomment to specify a particular user:
    # filter_config.target_user = "Jennifer Paul"
    
    # Adjust activity count if needed:
    # filter_config.max_recent_activities = 20
    
    data_filter = DataFilter(filter_config)
    
    # Select user
    target_user = data_filter.select_target_user(df, assigned_counts)
    if not target_user:
        return
    
    # Prepare data through filtering pipeline
    print("\n🔍 Applying filters and preparing data...")
    llm_data = data_filter.prepare_for_llm_analysis(df, target_user)
    
    if not llm_data:
        print("❌ No data available after filtering")
        return
    
    # Run AI analysis
    analysis = analyze_with_ai(llm_data, agent)
    
    if analysis:
        # Display results
        print_analysis_report(analysis)
        
        # Save results
        output_file = f"analysis_{target_user.replace(' ', '_')}.json"
        with open(output_file, 'w') as f:
            json.dump(analysis.model_dump(), f, indent=2)
        print(f"\n💾 Results saved to: {output_file}")
    else:
        print("❌ Analysis failed")

if __name__ == "__main__":
    main() 