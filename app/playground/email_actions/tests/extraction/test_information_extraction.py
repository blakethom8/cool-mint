#!/usr/bin/env python3
"""Test information extraction from emails in isolation"""
import os
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel

# Add parent directories to path
import sys
sys.path.insert(0, str(Path(__file__).parents[2]))

from utils.base import save_test_result, compare_results


class CallLogExtractionOutput(BaseModel):
    """Output schema for call log extraction"""
    subject: str = Field(..., description="Subject/title for the activity")
    description: str = Field(..., description="Detailed description of the activity")
    participants: List[dict] = Field(..., description="List of participants with names and roles")
    activity_date: Optional[str] = Field(None, description="When the activity occurred")
    duration_minutes: Optional[int] = Field(None, description="Duration in minutes")
    activity_type: str = Field(..., description="Type of activity (MD-to-MD, Sales Call, etc)")
    meeting_setting: str = Field("In-Person", description="In-Person, Virtual, Phone")
    
    # Specific fields for medical activities
    is_md_to_md: bool = Field(False, description="Whether this is an MD-to-MD activity")
    key_topics: List[str] = Field(default_factory=list, description="Key topics discussed")
    follow_up_items: List[str] = Field(default_factory=list, description="Follow-up items mentioned")


def test_extraction_prompt(prompt: str, test_cases: List[Dict]) -> List[Dict]:
    """Test information extraction with a specific prompt"""
    
    # Configure agent
    model = AnthropicModel("claude-3-5-sonnet-20241022")  # Use better model for extraction
    agent = Agent(
        system_prompt=prompt,
        result_type=CallLogExtractionOutput,
        model=model
    )
    
    results = []
    
    for test_case in test_cases:
        # Only test log_call cases
        if test_case.get('classification', {}).get('action_type') != 'log_call':
            continue
            
        email_content = test_case.get('email', {}).get('content', '')
        user_instruction = test_case.get('email', {}).get('user_instruction', '')
        
        if not email_content and not user_instruction:
            continue
        
        # Run extraction
        user_prompt = f"""Extract call/meeting information from this email:

User Instruction: {user_instruction}

Email content:
{email_content}

Extract all relevant information for logging this activity."""
        
        try:
            result = agent.run_sync(user_prompt=user_prompt)
            
            # Compare with expected extraction if available
            expected = test_case.get('extraction', {})
            
            extraction_result = {
                'email_id': test_case.get('email', {}).get('id'),
                'user_instruction': user_instruction[:100] if user_instruction else '',
                'extracted': {
                    'subject': result.output.subject,
                    'participants': result.output.participants,
                    'activity_date': result.output.activity_date,
                    'duration_minutes': result.output.duration_minutes,
                    'activity_type': result.output.activity_type,
                    'meeting_setting': result.output.meeting_setting,
                    'is_md_to_md': result.output.is_md_to_md,
                    'key_topics': result.output.key_topics
                },
                'expected': expected,
                'comparison': compare_extraction(expected, result.output) if expected else None
            }
            
            results.append(extraction_result)
            
        except Exception as e:
            results.append({
                'email_id': test_case.get('email', {}).get('id'),
                'error': str(e)
            })
    
    return results


def compare_extraction(expected: Dict, actual: CallLogExtractionOutput) -> Dict:
    """Compare expected vs actual extraction results"""
    comparison = {}
    
    # Check subject similarity
    if 'subject' in expected:
        comparison['subject_match'] = expected['subject'].lower() in actual.subject.lower()
    
    # Check if MD-to-MD detection is correct
    if 'mno_type' in expected:
        comparison['md_to_md_correct'] = (
            (expected['mno_type'] == 'MD_to_MD_Visits') == actual.is_md_to_md
        )
    
    # Check participant extraction
    if 'participants' in expected:
        expected_names = set([p.lower() for p in expected['participants'] if isinstance(p, str)])
        extracted_names = set([p.get('name', '').lower() for p in actual.participants])
        comparison['participants_found'] = len(expected_names.intersection(extracted_names))
        comparison['participants_expected'] = len(expected_names)
    
    return comparison


def test_prompt_variations():
    """Test different extraction prompts"""
    
    # Load test data
    test_data_path = Path(__file__).parent / 'test_data' / 'emails_with_actions.json'
    if not test_data_path.exists():
        print(f"Test data not found at {test_data_path}")
        return
        
    with open(test_data_path) as f:
        test_cases = json.load(f)
    
    # Define prompt variations
    prompts = {
        'baseline': """You are extracting information to log a call, meeting, or activity.

Extract the following information:
1. **Subject**: Brief title for the activity
2. **Description**: Detailed notes about what was discussed
3. **Participants**: All people involved (extract names and roles)
4. **Date**: When the activity occurred (if mentioned)
5. **Duration**: How long it lasted (if mentioned)
6. **Activity Type**: Type of activity (MD-to-MD, Sales Call, etc.)
7. **Setting**: In-person, Virtual, Phone, etc.

Be thorough in extracting discussion topics, action items, and follow-up plans.""",

        'improved_medical': """You are extracting information from a physician liaison's email to log medical activities.

CRITICAL: Identify if this is an MD-to-MD activity (physician-to-physician interaction).

Extract:
1. **Subject**: Create a clear, professional title
   - For MD-to-MD: Include "MD-to-MD" and both physicians' names
   - Example: "MD-to-MD: Dr. Smith with Dr. Jones - Cardiology Discussion"

2. **Participants**: Extract ALL names with their roles
   - Pay special attention to titles (Dr., MD, etc.)
   - Note their specialty or department if mentioned
   - Distinguish between internal (liaison/company) and external participants

3. **Activity Details**:
   - Date/time of the interaction
   - Duration (be specific if mentioned)
   - Setting (In-Person at hospital, Virtual, Phone, Lunch meeting, etc.)

4. **Clinical/Business Content**:
   - Key medical topics discussed
   - Patient care initiatives
   - Clinical programs or protocols
   - Business development opportunities

5. **Follow-up Actions**:
   - Next steps mentioned
   - Materials to send
   - Future meetings planned

Focus on medical context and physician relationships.""",

        'structured_extraction': """Extract physician liaison activity details for CRM logging.

PARSING INSTRUCTIONS:
1. First, scan for physician names (Dr./MD titles)
2. Identify temporal markers for dates/times
3. Look for activity type keywords: meeting, call, lunch, discussion
4. Extract specific medical/clinical context

OUTPUT REQUIREMENTS:
- Subject: [Activity Type]: [Participants] - [Main Topic]
- Is MD-to-MD: True if both participants are physicians
- Participants: [{name: "Dr. X", role: "Cardiologist", organization: "Hospital Y"}]
- Activity Date: Parse natural language dates (e.g., "last Tuesday" → specific date)
- Key Topics: List specific medical topics, not generic terms
- Setting: Be specific (e.g., "Lunch at hospital cafeteria" not just "In-Person")

MEDICAL CONTEXT CLUES:
- Specialty mentions (cardiology, oncology, etc.)
- Hospital/clinic names
- Clinical programs or protocols
- Patient population discussions
- Referral patterns"""
    }
    
    # Test each prompt
    all_results = {}
    
    for prompt_name, prompt in prompts.items():
        print(f"\nTesting extraction prompt: {prompt_name}")
        results = test_extraction_prompt(prompt, test_cases)
        all_results[prompt_name] = results
        
        # Show sample extractions
        for r in results[:2]:  # Show first 2
            if 'extracted' in r:
                print(f"\n  Email: {r['user_instruction']}")
                print(f"  Subject: {r['extracted']['subject']}")
                print(f"  Participants: {len(r['extracted']['participants'])} found")
                print(f"  MD-to-MD: {r['extracted']['is_md_to_md']}")
                
                if r['comparison']:
                    print(f"  Comparison: {r['comparison']}")
    
    # Save results
    filename = save_test_result('information_extraction', {
        'test_cases': len([tc for tc in test_cases if tc.get('classification', {}).get('action_type') == 'log_call']),
        'prompts_tested': list(prompts.keys()),
        'results': all_results
    })
    
    print(f"\nResults saved to: results/{filename}")


def test_specific_scenarios():
    """Test specific extraction scenarios"""
    
    # Define the best prompt for scenario testing
    improved_medical_prompt = """You are extracting information from a physician liaison's email to log medical activities.

CRITICAL: Identify if this is an MD-to-MD activity (physician-to-physician interaction).

Extract:
1. **Subject**: Create a clear, professional title
   - For MD-to-MD: Include "MD-to-MD" and both physicians' names
   - Example: "MD-to-MD: Dr. Smith with Dr. Jones - Cardiology Discussion"

2. **Participants**: Extract ALL names with their roles
   - Pay special attention to titles (Dr., MD, etc.)
   - Note their specialty or department if mentioned
   - Distinguish between internal (liaison/company) and external participants

3. **Activity Details**:
   - Date/time of the interaction
   - Duration (be specific if mentioned)
   - Setting (In-Person at hospital, Virtual, Phone, Lunch meeting, etc.)

4. **Clinical/Business Content**:
   - Key medical topics discussed
   - Patient care initiatives
   - Clinical programs or protocols
   - Business development opportunities

5. **Follow-up Actions**:
   - Next steps mentioned
   - Materials to send
   - Future meetings planned

Focus on medical context and physician relationships."""
    
    scenarios = [
        {
            'name': 'md_to_md_lunch',
            'instruction': 'log MD-to-MD lunch with Dr. Sarah Johnson from Cedars',
            'content': """
Had a great lunch meeting with Dr. Sarah Johnson, the new cardiology chief at Cedars-Sinai.
We discussed their new cardiac screening program and opportunities for collaboration.
She mentioned they're looking to expand their referral network. Meeting lasted about 90 minutes
at the hospital cafeteria. Need to send her our capabilities deck by Friday.
            """,
            'expected': {
                'is_md_to_md': True,
                'participants': ['Dr. Sarah Johnson'],
                'duration': 90,
                'setting': 'In-Person',
                'follow_up': True
            }
        },
        {
            'name': 'virtual_meeting_multiple_participants',
            'instruction': 'log virtual meeting with oncology team',
            'content': """
Just finished a Teams call with the oncology team at Regional Medical Center.
Participants:
- Dr. Michael Chen (Oncology Director)
- Dr. Lisa Park (Medical Oncologist) 
- Jane Smith (Oncology Nurse Manager)
- Myself

Discussed their new clinical trial enrollment process and how we can help increase
physician awareness. Call was scheduled for 30 minutes but ran 45 minutes due to
good discussion. They want us to present at their next tumor board meeting.
            """,
            'expected': {
                'participants': ['Dr. Michael Chen', 'Dr. Lisa Park', 'Jane Smith'],
                'duration': 45,
                'setting': 'Virtual',
                'activity_type': 'Team Meeting'
            }
        }
    ]
    
    print("\nTesting specific extraction scenarios...")
    
    # Use the best prompt
    model = AnthropicModel("claude-3-5-sonnet-20241022")
    agent = Agent(
        system_prompt=improved_medical_prompt,
        result_type=CallLogExtractionOutput,
        model=model
    )
    
    for scenario in scenarios:
        user_prompt = f"""Extract call/meeting information:

User Instruction: {scenario['instruction']}

Email content:
{scenario['content']}"""
        
        result = agent.run_sync(user_prompt=user_prompt)
        
        print(f"\n{scenario['name']}:")
        print(f"  Subject: {result.output.subject}")
        print(f"  Participants: {[p['name'] for p in result.output.participants]}")
        print(f"  Duration: {result.output.duration_minutes} minutes")
        print(f"  Setting: {result.output.meeting_setting}")
        print(f"  MD-to-MD: {result.output.is_md_to_md}")
        print(f"  Key Topics: {result.output.key_topics[:2]}")  # First 2 topics


if __name__ == '__main__':
    print("Testing information extraction...")
    
    # Check if API key is set
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY not set in environment")
        exit(1)
    
    test_prompt_variations()
    test_specific_scenarios()