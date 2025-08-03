#!/usr/bin/env python3
"""Utility for testing prompt variations"""
import json
from pathlib import Path
from typing import Dict, List, Callable
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel

# Add parent directories to path
import sys
sys.path.insert(0, str(Path(__file__).parents[2]))

from utils.base import save_test_result


class PromptVariation:
    """Represents a prompt variation to test"""
    def __init__(self, name: str, prompt: str, description: str = ""):
        self.name = name
        self.prompt = prompt
        self.description = description


class PromptTester:
    """Tests multiple prompt variations against test cases"""
    
    def __init__(self, output_type: type[BaseModel], model_name: str = "claude-3-5-haiku-20241022"):
        self.output_type = output_type
        self.model = AnthropicModel(model_name)
        self.results = {}
    
    def add_variation(self, variation: PromptVariation):
        """Add a prompt variation to test"""
        self.results[variation.name] = {
            'prompt': variation.prompt,
            'description': variation.description,
            'test_results': []
        }
    
    def test_prompts(self, test_cases: List[Dict], 
                    user_prompt_builder: Callable[[Dict], str],
                    result_evaluator: Callable[[Dict, BaseModel], Dict] = None):
        """Test all prompt variations against test cases"""
        
        for variation_name, variation_data in self.results.items():
            print(f"\nTesting prompt variation: {variation_name}")
            
            agent = Agent(
                system_prompt=variation_data['prompt'],
                result_type=self.output_type,
                model=self.model
            )
            
            for test_case in test_cases:
                try:
                    # Build user prompt from test case
                    user_prompt = user_prompt_builder(test_case)
                    
                    # Run agent
                    result = agent.run_sync(user_prompt=user_prompt)
                    
                    # Evaluate result if evaluator provided
                    evaluation = {}
                    if result_evaluator:
                        evaluation = result_evaluator(test_case, result.output)
                    
                    variation_data['test_results'].append({
                        'test_case_id': test_case.get('id', 'unknown'),
                        'success': True,
                        'output': result.output.model_dump(),
                        'evaluation': evaluation
                    })
                    
                except Exception as e:
                    variation_data['test_results'].append({
                        'test_case_id': test_case.get('id', 'unknown'),
                        'success': False,
                        'error': str(e)
                    })
    
    def get_summary(self) -> Dict:
        """Get summary of test results"""
        summary = {}
        
        for variation_name, data in self.results.items():
            successful = sum(1 for r in data['test_results'] if r['success'])
            total = len(data['test_results'])
            
            # Calculate custom metrics from evaluations
            evaluations = [r['evaluation'] for r in data['test_results'] if r.get('evaluation')]
            
            summary[variation_name] = {
                'success_rate': successful / total if total > 0 else 0,
                'total_tests': total,
                'successful_tests': successful,
                'custom_metrics': self._aggregate_evaluations(evaluations)
            }
        
        return summary
    
    def _aggregate_evaluations(self, evaluations: List[Dict]) -> Dict:
        """Aggregate evaluation metrics"""
        if not evaluations:
            return {}
        
        # Simple aggregation - can be customized
        metrics = {}
        
        # Find common keys
        all_keys = set()
        for eval_dict in evaluations:
            all_keys.update(eval_dict.keys())
        
        for key in all_keys:
            values = [e.get(key) for e in evaluations if key in e]
            
            # Handle different types
            if all(isinstance(v, bool) for v in values):
                metrics[f"{key}_true_rate"] = sum(values) / len(values)
            elif all(isinstance(v, (int, float)) for v in values):
                metrics[f"{key}_avg"] = sum(values) / len(values)
        
        return metrics
    
    def save_results(self, test_name: str) -> str:
        """Save results to file"""
        return save_test_result(f"prompt_variations_{test_name}", {
            'variations': list(self.results.keys()),
            'summary': self.get_summary(),
            'detailed_results': self.results
        })


# Example usage function
def example_usage():
    """Example of how to use the PromptTester"""
    from pydantic import Field
    
    # Define output schema
    class SimpleClassification(BaseModel):
        category: str = Field(..., description="Category classification")
        confidence: float = Field(..., description="Confidence score 0-1")
    
    # Create tester
    tester = PromptTester(SimpleClassification)
    
    # Add variations
    tester.add_variation(PromptVariation(
        name="simple",
        prompt="Classify the input into categories: A, B, or C",
        description="Basic classification prompt"
    ))
    
    tester.add_variation(PromptVariation(
        name="detailed",
        prompt="""You are a classification expert. 
        Carefully analyze the input and classify into:
        - Category A: Technical content
        - Category B: Business content  
        - Category C: Other content
        Provide high confidence scores only when certain.""",
        description="Detailed classification with explanations"
    ))
    
    # Test cases
    test_cases = [
        {"id": "1", "text": "Python programming tutorial"},
        {"id": "2", "text": "Quarterly revenue report"},
        {"id": "3", "text": "Recipe for chocolate cake"}
    ]
    
    # Define how to build prompts
    def build_prompt(test_case):
        return f"Classify this text: {test_case['text']}"
    
    # Define evaluation
    def evaluate(test_case, output):
        # Example evaluation logic
        return {
            'high_confidence': output.confidence > 0.8,
            'confidence_score': output.confidence
        }
    
    # Run tests
    tester.test_prompts(test_cases, build_prompt, evaluate)
    
    # Get and print summary
    summary = tester.get_summary()
    print("\nSummary:")
    for variation, metrics in summary.items():
        print(f"\n{variation}:")
        print(f"  Success rate: {metrics['success_rate']:.2%}")
        print(f"  Custom metrics: {metrics['custom_metrics']}")
    
    # Save results
    filename = tester.save_results("example")
    print(f"\nResults saved to: {filename}")


if __name__ == '__main__':
    print("Prompt Variation Testing Utility")
    print("=" * 50)
    print("\nThis utility helps test different prompt variations.")
    print("Import and use PromptTester class in your tests.")
    print("\nRunning example...")
    example_usage()