# Procedure Code Classification System

## Overview
This system provides an automated workflow for categorizing medical procedures by complexity using SQL data extraction, LLM-based analysis, and structured output. The system classifies procedures into three complexity levels: High, Medium, and Low.

## System Components

### 1. SQL Data Extraction (`proc_code_sql_template.py`)
- Defines SQL templates for querying procedure codes
- Primary template: `surgical_cardio_procedures`
- Extracts procedure codes, descriptions, types, and visit volumes

### 2. Data Formatting (`sql_result_formatter.py`)
- Transforms SQL results into LLM-friendly format
- Includes procedure metadata and statistics
- Structures data for consistent LLM analysis

### 3. LLM Categorization (`proc_detail_cat_agent.py`)
- Uses GPT-4 for complexity analysis
- Provides detailed rationale for each categorization
- Includes confidence scores for decisions
- Generates overall insights and distribution statistics

### 4. Workflow Orchestration (`run_categorization_workflow.py`)
The main workflow coordinator that ties everything together:

```python
def run_complete_workflow():
    1. run_sql_query()      # Extract procedure data
    2. format_for_llm()     # Prepare for LLM
    3. categorize_with_llm() # Run LLM analysis
    4. display_results()     # Show findings
```

## Configuration

```python
# Key configuration parameters
TEMPLATE_ID = "surgical_cardio_procedures"
PARAMETERS = {
    "limit": 10  # Number of procedures to analyze
}
```

## Output Structure

The system provides:
1. **Individual Procedure Analysis**
   - Complexity category (High/Medium/Low)
   - Confidence score
   - Detailed rationale
   - Visit volume

2. **Aggregate Insights**
   - Category distribution
   - Key insights
   - Overall confidence score

## Example Output Format
```
🏥 CATEGORIZED PROCEDURES:
1. 33533 - HIGH COMPLEXITY
   Description: Coronary artery bypass
   Visit Volume: 3,500
   Confidence: 0.95
   Rationale:
     • Major surgical procedure
     • Requires specialized skills
     • High risk of complications

📈 COMPLEXITY DISTRIBUTION:
   High   : 2 procedures (40.0%)
   Medium : 2 procedures (40.0%)
   Low    : 1 procedures (20.0%)
```

## Usage

1. **Setup**
   ```bash
   # Set environment variables
   DATABASE_URL=postgresql://...
   OPENAI_API_KEY=your-key
   ```

2. **Run Analysis**
   ```bash
   python run_categorization_workflow.py
   ```

3. **Customize**
   - Modify `PARAMETERS` for different batch sizes
   - Adjust SQL template for different procedure types
   - Configure LLM settings in proc_detail_cat_agent.py

## Dependencies
- Python 3.8+
- SQLAlchemy
- Pandas
- OpenAI GPT-4
- Pydantic
- Python-dotenv

## File Structure
```
sql_proc_code/
├── run_categorization_workflow.py  # Main workflow
├── proc_code_sql_template.py      # SQL queries
└── proc_detail_cat_agent.py       # LLM agent
```

## Error Handling
The workflow includes comprehensive error handling:
- SQL query failures
- Data formatting issues
- LLM processing errors
- Empty result handling

## Performance Considerations
- Batch processing available through PARAMETERS["limit"]
- LLM calls are synchronous for reliability
- Database connection pooling implemented
- Results displayed in real-time as processing occurs

## Future Improvements
1. Add caching for repeated categorizations
2. Implement async processing for larger batches
3. Add more complexity categories
4. Store categorization results in database
5. Add API endpoint for remote access
