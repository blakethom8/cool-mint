# Monthly SFDC Activity Summary - Playground

This folder contains test scripts and utilities for the Monthly Activity Summary Workflow that analyzes Salesforce activity data.

## Contents

### `test_monthly_activity_summary.py`
Comprehensive test script for the monthly activity summary workflow.

**Features:**
- Schema validation testing
- End-to-end workflow execution
- Detailed result analysis and reporting
- JSON export of complete results
- Error handling validation

**Usage:**
```bash
# From the project root directory
cd playground/monthly_sfdc_activity_summary
python test_monthly_activity_summary.py
```

**Requirements:**
- Valid database connection with Salesforce data
- OpenAI API key configured
- Real Salesforce user ID with activity data

## Workflow Overview

The Monthly Activity Summary Workflow processes Salesforce activity data through 4 sequential nodes:

1. **Request Category Node** - Categorizes the request type
2. **SQL Data Node** - Retrieves activity data with complex joins
3. **Data Structure Node** - Organizes data for LLM consumption
4. **LLM Summary Node** - Generates comprehensive summaries using OpenAI

## Test Data Requirements

To run the full workflow test, you need:
- A valid Salesforce user ID (15-18 characters)
- Activity data in your `sf_activities` table
- Contact data in your `sf_contacts` table
- User data in your `sf_users` table

## Output

The test script generates:
- Console output with detailed progress and results
- JSON file with complete workflow results
- Performance metrics and error reporting
- Sample insights from the generated summary

## Adding New Tests

Create additional test files in this folder for:
- Performance testing
- Edge case validation
- Different date ranges
- Multiple user scenarios
- Error condition testing

## Related Files

The workflow implementation is located in:
- `app/workflows/monthly_activity_summary_workflow.py`
- `app/workflows/monthly_activity_summary_nodes/`
- `app/schemas/monthly_activity_summary_schema.py`
- `app/prompts/monthly_activity_summary/` 