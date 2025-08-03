# Email Actions Test Guide

This directory contains organized test scripts for the email actions workflow with entity matching.

## Main Test Scripts

### 1. `test_production_workflow.py` - Production Tests (WITH Database Commits)
```bash
# Run all tests (will prompt for confirmation)
python test_production_workflow.py

# Run specific test type
python test_production_workflow.py --test call
python test_production_workflow.py --test note
python test_production_workflow.py --test reminder

# Test with real emails from sample_emails.json
python test_production_workflow.py --sample-emails

# Skip confirmation (use with caution!)
python test_production_workflow.py --skip-confirmation
python test_production_workflow.py --sample-emails --skip-confirmation
```

**⚠️ WARNING**: This script WILL create records in the database. Use with caution!

### 2. `test_workflow_dry_run.py` - Dry Run Tests (NO Database Commits)
```bash
# Run all standard tests
python test_workflow_dry_run.py

# Run specific test by name
python test_workflow_dry_run.py --test "Call Log"

# Test with sample emails only
python test_workflow_dry_run.py --sample-emails

# Include sample emails with standard tests
python test_workflow_dry_run.py --include-samples

# Verbose output
python test_workflow_dry_run.py --verbose
```

**✅ SAFE**: Uses testing node - no database changes will be made.

### 3. `test_quick.py` - Quick Interactive Tests
```bash
# Quick test with content
python test_quick.py "Log call with Dr. Smith"

# With custom subject and instruction
python test_quick.py "Meeting notes" -s "MD-to-MD Meeting" -i "Log this call"

# Interactive mode
python test_quick.py --interactive

# Run entity matching tests
python test_quick.py --entity-test

# Run edge case tests
python test_quick.py --edge-cases

# Test with sample emails from JSON file
python test_quick.py --sample-emails

# Use production workflow (commits to DB)
python test_quick.py "Add note about Dr. Johnson" --production
```

## Test Organization

### `tests/` - Organized test files by category

- **`entity_matching/`** - Entity matching specific tests
  - `test_contact_matcher.py` - Contact matching tests
  - `test_note_entity_matching.py` - Note-specific entity tests
  - `test_reminder_entity_matching.py` - Reminder-specific tests
  - `test_call_log_entity_matching.py` - Call log entity tests
  - `contact_matcher.py`, `contact_matcher_v2.py` - Matching implementations

- **`extraction/`** - Data extraction tests
  - `test_information_extraction.py` - General extraction tests
  - `test_log_call_extraction_simple.py` - Call log extraction

- **`classification/`** - Intent classification tests
  - `test_intent_classification.py` - Full classification tests
  - `test_intent_classification_simple.py` - Simple classification

- **`utils/`** - Utility scripts
  - `debug_email_actions.py` - Debug database records
  - `extract_test_data.py` - Extract test data from DB
  - `data_validator.py` - Validate test data
  - `scoring.py` - Scoring utilities

## Workflow Features Tested

All test scripts verify:
1. **Intent Classification** - Correct action type detection
2. **Entity Extraction** - Identifying people and organizations
3. **Entity Matching** - Matching to database records
4. **Single Record Pattern** - One staging record per email for all action types
5. **JSONB Storage** - All entities stored in JSONB fields

## Key Differences Between Workflows

- **Production Workflow** (`test_production_workflow.py`)
  - Uses `CreateStagingRecordNode`
  - Creates real database records
  - Shows actual database IDs

- **Dry Run Workflow** (`test_workflow_dry_run.py`)
  - Uses `CreateStagingRecordTestingNode`
  - Simulates database operations
  - Safe for testing

## Entity Matching Behavior

All action types now follow the same pattern:
- **Call Logs**: Single record, participants in `matched_participant_ids` JSONB
- **Notes**: Single record, entities in `matched_entity_ids` JSONB
- **Reminders**: Single record, entities in `matched_entity_ids` JSONB

## Testing with Sample Emails

All three main test scripts support testing with real email data from `test_data/sample_emails.json`:

- `test_quick.py --sample-emails` - Quick test of sample emails
- `test_workflow_dry_run.py --sample-emails` - Dry run with sample emails
- `test_production_workflow.py --sample-emails` - Production test (creates DB records!)

This allows you to:
1. Test the end-to-end workflow with real email examples
2. Verify entity matching with actual email content
3. Ensure consistent behavior across different email types

## Next Steps

1. Use `test_workflow_dry_run.py` for safe testing
2. Use `test_quick.py` for quick debugging
3. Use `test_production_workflow.py` when ready to create real staging records
4. Check staging tables and approve/reject records as needed
5. Add new test emails to `test_data/sample_emails.json` as needed