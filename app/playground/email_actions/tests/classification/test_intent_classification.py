#!/usr/bin/env python3
"""Test intent classification in isolation"""
import os
import json
from pathlib import Path
from typing import Dict, List
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel

# Add parent directories to path
import sys
sys.path.insert(0, str(Path(__file__).parents[2]))

from utils.base import save_test_result, load_prompt_template


class IntentClassificationOutput(BaseModel):
    """Output schema for intent classification"""
    action_type: str = Field(..., description="One of: add_note, log_call, set_reminder, unknown")
    confidence_score: float = Field(..., description="Confidence in classification (0-1)")
    reasoning: str = Field(..., description="Explanation of why this classification was chosen")
    keywords_found: List[str] = Field(default_factory=list, description="Key phrases that influenced the decision")


def test_classification_prompt(prompt: str, test_cases: List[Dict]) -> List[Dict]:
    """Test a specific prompt against test cases"""
    
    # Configure agent with Anthropic model
    model = AnthropicModel("claude-3-5-haiku-20241022")
    agent = Agent(
        system_prompt=prompt,
        result_type=IntentClassificationOutput,
        model=model
    )
    
    results = []
    
    for test_case in test_cases:
        # Prepare email content
        email_content = test_case.get('email', {}).get('content', '')
        user_instruction = test_case.get('email', {}).get('user_instruction', '')
        
        if not email_content and not user_instruction:
            continue
        
        # Run classification
        user_prompt = f"""Classify this email request:

User Instruction: {user_instruction}

Email Content:
{email_content}

Determine the primary action being requested."""
        
        try:
            result = agent.run_sync(user_prompt=user_prompt)
            
            # Compare with expected if available
            expected_action = test_case.get('classification', {}).get('action_type')
            
            results.append({
                'email_id': test_case.get('email', {}).get('id'),
                'user_instruction': user_instruction[:100] if user_instruction else '',
                'predicted': result.output.action_type,
                'expected': expected_action,
                'correct': result.output.action_type == expected_action if expected_action else None,
                'confidence': result.output.confidence_score,
                'reasoning': result.output.reasoning,
                'keywords': result.output.keywords_found
            })
            
        except Exception as e:
            results.append({
                'email_id': test_case.get('email', {}).get('id'),
                'error': str(e)
            })
    
    return results


def test_prompt_variations():
    """Test different prompt variations"""
    
    # Load test data
    test_data_path = Path(__file__).parent / 'test_data' / 'emails_with_actions.json'
    if not test_data_path.exists():
        print(f"Test data not found at {test_data_path}")
        return
        
    with open(test_data_path) as f:
        test_cases = json.load(f)
    
    # Define prompt variations
    prompts = {
        'baseline': """You are an AI assistant that classifies emails into specific action types.
            
Analyze the email content and determine which ONE primary action the user is requesting:

1. **add_note**: User wants to capture information, thoughts, or meeting notes
   - Keywords: "capture notes", "document", "record information", "make a note"

2. **log_call**: User wants to log a call, meeting, or MD-to-MD activity
   - Keywords: "log activity", "log call", "log meeting", "MD-to-MD", "capture meeting"

3. **set_reminder**: User wants to create a reminder or follow-up task
   - Keywords: "remind me", "follow up", "check back", "schedule reminder"

If multiple actions could apply, choose the PRIMARY/MAIN action being requested.
If no clear action matches, use "unknown".""",
        
        'improved_v1': """You are an AI assistant for a medical CRM system that classifies physician liaison emails.

Analyze the user's instruction and email content to determine the PRIMARY action requested:

1. **log_call**: Log any physician interaction, meeting, or MD-to-MD activity
   - Key indicators: "log", "had a meeting", "met with", "MD-to-MD", "lunch", "call", "discussion"
   - Medical context: physician names, hospital references, clinical discussions
   
2. **add_note**: Capture information or observations without logging an activity
   - Key indicators: "note", "capture", "document", "record" (without meeting context)
   - General information that needs to be saved
   
3. **set_reminder**: Create a follow-up task or reminder
   - Key indicators: "remind", "follow up", "check back", time references like "in X days"
   
4. **unknown**: When the intent is unclear or doesn't match above categories

Focus on the USER INSTRUCTION first, then use email content for context.
Look for medical/clinical context that suggests physician interactions.""",
        
        'improved_v2': """You classify emails in a physician liaison CRM system.

USER INSTRUCTION is the primary signal - it tells you what the user wants to do.
Email content provides context but the instruction takes precedence.

Actions:
- **log_call**: Any physician meeting, call, or MD-to-MD interaction that occurred
- **add_note**: Save information without logging an activity
- **set_reminder**: Create a future task or follow-up
- **unknown**: Intent unclear

Decision process:
1. Parse the user instruction for action verbs
2. Look for temporal clues (past = likely log_call, future = likely set_reminder)
3. Identify medical context (physician names, clinical topics)
4. Choose the most specific matching action"""
    }
    
    # Test each prompt
    all_results = {}
    
    for prompt_name, prompt in prompts.items():
        print(f"\nTesting prompt: {prompt_name}")
        results = test_classification_prompt(prompt, test_cases)
        all_results[prompt_name] = results
        
        # Calculate accuracy
        correct = sum(1 for r in results if r.get('correct') == True)
        total = sum(1 for r in results if r.get('correct') is not None)
        accuracy = correct / total if total > 0 else 0
        
        print(f"Accuracy: {accuracy:.2%} ({correct}/{total})")
        
        # Show misclassifications
        for r in results:
            if r.get('correct') == False:
                print(f"  Misclassified: '{r['user_instruction']}' as {r['predicted']} (expected: {r['expected']})")
    
    # Save results
    filename = save_test_result('intent_classification', {
        'test_cases': len(test_cases),
        'prompts_tested': list(prompts.keys()),
        'results': all_results
    })
    
    print(f"\nResults saved to: results/{filename}")


def test_edge_cases():
    """Test specific edge cases"""
    
    edge_cases = [
        {
            'name': 'ambiguous_note_vs_log',
            'instruction': 'capture the meeting notes from our discussion with Dr. Smith',
            'expected': 'log_call',  # Meeting implies an activity to log
            'reasoning': 'Contains both "capture notes" and "meeting" - should prioritize logging the activity'
        },
        {
            'name': 'past_vs_future',
            'instruction': 'log a reminder to follow up with Dr. Johnson',
            'expected': 'set_reminder',  # "reminder" is the key action despite "log"
            'reasoning': 'The word "reminder" should override "log"'
        },
        {
            'name': 'multiple_actions',
            'instruction': 'log the call with Dr. Brown and remind me to send the materials in 2 weeks',
            'expected': 'log_call',  # Primary action should be identified
            'reasoning': 'Multiple actions present, should identify the primary one'
        }
    ]
    
    print("\nTesting edge cases...")
    
    # Define prompt for edge case testing
    improved_prompt = """You classify emails in a physician liaison CRM system.

USER INSTRUCTION is the primary signal - it tells you what the user wants to do.
Email content provides context but the instruction takes precedence.

Actions:
- **log_call**: Any physician meeting, call, or MD-to-MD interaction that occurred
- **add_note**: Save information without logging an activity
- **set_reminder**: Create a future task or follow-up
- **unknown**: Intent unclear

Decision process:
1. Parse the user instruction for action verbs
2. Look for temporal clues (past = likely log_call, future = likely set_reminder)
3. Identify medical context (physician names, clinical topics)
4. Choose the most specific matching action"""
    
    # Use the improved prompt
    model = AnthropicModel("claude-3-5-haiku-20241022")
    agent = Agent(
        system_prompt=improved_prompt,
        result_type=IntentClassificationOutput,
        model=model
    )
    
    for case in edge_cases:
        result = agent.run_sync(
            user_prompt=f"User Instruction: {case['instruction']}"
        )
        
        print(f"\nCase: {case['name']}")
        print(f"Instruction: {case['instruction']}")
        print(f"Expected: {case['expected']}")
        print(f"Predicted: {result.output.action_type}")
        print(f"Confidence: {result.output.confidence_score:.2f}")
        print(f"Correct: {'✓' if result.output.action_type == case['expected'] else '✗'}")
        print(f"Reasoning: {result.output.reasoning}")


if __name__ == '__main__':
    print("Testing intent classification...")
    
    # Check if API key is set
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY not set in environment")
        exit(1)
    
    test_prompt_variations()
    test_edge_cases()