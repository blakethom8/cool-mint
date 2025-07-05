"""
Simple Outreach Data Processor and LLM Analyzer
Processes Salesforce outreach data and prepares it for LLM analysis.
"""

import pandas as pd
from typing import Dict, List, Any
import json
from datetime import datetime
from pathlib import Path
import openai
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class OutreachActivity:
    """Represents a single outreach activity with all participants"""
    activity_date: str
    bd_specialist: str
    subject: str
    outreach_type: str
    outreach_subtype: str
    comments: str
    participants: List[Dict[str, str]]  # List of participants with their details
    account_name: str

def load_excel_data(file_path: str) -> pd.DataFrame:
    """Load the Excel file into a pandas DataFrame"""
    return pd.read_excel(file_path)

def group_activities(df: pd.DataFrame) -> List[OutreachActivity]:
    """
    Group multiple rows of the same activity into single OutreachActivity objects.
    Each unique activity (same date, specialist, subject) will be one entry with all participants.
    """
    # Create a unique identifier for each activity
    df['activity_id'] = df.apply(
        lambda x: f"{x['Activity Date']}_{x['BD Specialists']}_{x['Subject']}", 
        axis=1
    )
    
    activities = []
    
    # Group by activity_id
    for _, group in df.groupby('activity_id'):
        # Get the first row for activity details
        first_row = group.iloc[0]
        
        # Collect all participants
        participants = []
        for _, row in group.iterrows():
            participant = {
                'name': str(row['Name']),
                'specialty': str(row['Specialty']),
                'sub_network': str(row['Sub-Network'])
            }
            participants.append(participant)
        
        # Create OutreachActivity object
        activity = OutreachActivity(
            activity_date=first_row['Activity Date'].strftime('%Y-%m-%d'),
            bd_specialist=str(first_row['BD Specialists']),
            subject=str(first_row['Subject']),
            outreach_type=str(first_row['Outreach Type']),
            outreach_subtype=str(first_row['Outreach subtype']),
            comments=str(first_row['Comments_short_c']),
            participants=participants,
            account_name=str(first_row['Account name'])
        )
        activities.append(activity)
    
    return activities

def prepare_for_llm(activities: List[OutreachActivity]) -> Dict[str, Any]:
    """
    Convert activities into a format suitable for LLM analysis
    """
    return {
        'metadata': {
            'total_activities': len(activities),
            'date_range': {
                'start': min(a.activity_date for a in activities),
                'end': max(a.activity_date for a in activities)
            }
        },
        'activities': [
            {
                'date': activity.activity_date,
                'specialist': activity.bd_specialist,
                'type': {
                    'main': activity.outreach_type,
                    'sub': activity.outreach_subtype
                },
                'subject': activity.subject,
                'comments': activity.comments,
                'participants': activity.participants,
                'account': activity.account_name
            }
            for activity in activities
        ]
    }

def save_json(data: Dict[str, Any], output_path: str):
    """Save the processed data as JSON"""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def main(input_file: str, output_file: str):
    """Main function to process the outreach data"""
    # Load data
    df = load_excel_data(input_file)
    
    # Group activities
    activities = group_activities(df)
    
    # Prepare for LLM
    llm_ready_data = prepare_for_llm(activities)
    
    # Save results
    save_json(llm_ready_data, output_file)
    print(f"Processed {len(activities)} unique activities.")
    print(f"Results saved to {output_file}")

if __name__ == "__main__":
    input_file = "sara_outreach_efforts.xlsx"
    output_file = "processed_outreach.json"
    main(input_file, output_file) 