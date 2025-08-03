# Email Actions Playground

This directory contains isolated testing scripts for refining the email actions workflow.

## Directory Structure

```
email_actions/
├── test_data/        # Sample emails and expected outputs
├── prompts/          # Prompt variations and templates
├── results/          # Test results and metrics
├── utils/            # Shared utilities for testing
└── *.py              # Individual test scripts
```

## Test Scripts

- `test_intent_classification.py` - Test email intent classification
- `test_information_extraction.py` - Test field extraction from emails
- `test_participant_matching.py` - Match extracted participants to CRM
- `test_date_parsing.py` - Test date/time extraction
- `test_mno_classification.py` - Test activity type classification

## Usage

Each script can be run independently:
```bash
python playground/email_actions/test_intent_classification.py
```

## Goals

1. Improve classification accuracy
2. Enhance information extraction quality
3. Build validation layers
4. Create feedback mechanisms
5. Test different models and prompts