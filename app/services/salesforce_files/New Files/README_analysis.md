# Healthcare Outreach Specialty Analysis

This project analyzes healthcare outreach specialist activities to understand specialty targeting patterns using AI-powered analysis with pydantic_ai and OpenAI.

## Overview

The system processes Excel reports containing outreach activity data and uses Large Language Models to analyze:
- Which medical specialties outreach specialists are targeting
- Outreach patterns and strategies
- Effectiveness indicators
- Key insights about specialty focus

## Features

- 📊 **Excel Data Processing**: Handles HTML-formatted Excel exports from healthcare systems
- 🤖 **AI-Powered Analysis**: Uses pydantic_ai with OpenAI GPT models for intelligent analysis
- 🎯 **Specialty Targeting**: Identifies top medical specialties being targeted
- 📈 **Pattern Recognition**: Discovers outreach strategies and patterns
- 📋 **Comprehensive Reports**: Generates detailed analysis reports
- 💾 **Export Results**: Saves analysis results to JSON format

## Setup

### 1. Virtual Environment
Activate your virtual environment:
```powershell
.\\venv\\Scripts\\Activate.ps1
```

### 2. Dependencies
Install required packages:
```bash
pip install -r requirements.txt
```

### 3. OpenAI API Key
You need an OpenAI API key to run the analysis. Set it up using one of these methods:

**Option A: Environment Variable (Recommended)**
```powershell
$env:OPENAI_API_KEY='your_api_key_here'
```

**Option B: Create a .env file**
```
OPENAI_API_KEY=your_api_key_here
```

Get your API key from: https://platform.openai.com/api-keys

## Usage

### Basic Analysis
Run the analysis on your Excel report:
```bash
python outreach_analyzer.py
```

This will:
1. Load the Excel file (`report1749182913520.xls`)
2. Process the HTML-formatted data
3. Analyze the outreach specialist with the most activities
4. Generate an AI-powered specialty targeting report

### Understanding the Data
To explore your data structure:
```bash
python excel_processor.py
```

This shows:
- Column structure
- Available assigned users
- Activity counts and distributions
- Sample data records

### Configuration Check
To verify your OpenAI setup:
```bash
python config.py
```

## File Structure

- `outreach_analyzer.py` - Main analysis script with pydantic_ai integration
- `excel_processor.py` - Excel data processing and filtering
- `config.py` - Configuration and API key setup
- `requirements.txt` - Python dependencies
- `report1749182913520.xls` - Your Excel data file

## Output

The analysis generates:

### Console Report
- 📊 Activity overview with total counts
- 🎯 Top medical specialties targeted
- 📈 Outreach patterns and strategies  
- 💡 Key insights from AI analysis
- 📋 Specialty focus summary

### JSON Export
Results are saved to `analysis_result_[username].json` containing:
- Structured analysis data
- Top specialties with details
- Outreach patterns list
- Key insights array
- Comprehensive summary

## Example Output

```
🏥 Healthcare Outreach Specialty Analysis
==================================================
✅ OpenAI API key is configured

📈 Data Overview:
   User: Sara Murphy
   Total Activities: 940
   Recent Activities for Analysis: 15

================================================================================
SPECIALTY TARGETING ANALYSIS REPORT
Healthcare Outreach Specialist: Sara Murphy
================================================================================

📊 ACTIVITY OVERVIEW:
   Total Activities Analyzed: 940

🎯 TOP SPECIALTIES TARGETED:
   • Internal & Family Medicine: 149 activities (Primary care focus)
   • OB/GYN: 143 activities (Women's health emphasis)
   • Oncology - Surgical: 84 activities (Cancer care specialization)

📈 OUTREACH PATTERNS:
   • BD Outreach: 335 activities (Primary method)
   • MD-to-MD Visits: 264 activities (Direct physician engagement)
   • Events: 87 activities (Community engagement)

💡 KEY INSIGHTS:
   • Strong focus on primary care and women's health
   • Balanced approach between direct visits and broader outreach
   • Consistent engagement with oncology specialists

📋 SPECIALTY FOCUS SUMMARY:
   Sara Murphy demonstrates a strategic approach focusing primarily on...
```

## Troubleshooting

### Common Issues

**File encoding errors:**
- The system auto-detects encoding and tries multiple formats
- HTML-formatted Excel files are supported

**API errors:**
- Verify your OpenAI API key is correctly set
- Check your internet connection
- Ensure you have API credits available

**Data processing errors:**
- Verify the Excel file is in the correct location
- Check that the file contains the expected columns

## Customization

### Analyzing Different Users
Modify the `assigned_user` variable in `outreach_analyzer.py`:
```python
assigned_user = "Jennifer Paul"  # Specific user
assigned_user = None            # Auto-select user with most activities
```

### Adjusting Analysis Depth
Change the number of recent activities analyzed:
```python
llm_data = prepare_data_for_llm(df, assigned_user, max_records=20)
```

### Modifying AI Model
Update the model in `outreach_analyzer.py`:
```python
outreach_agent = Agent(
    model='openai:gpt-4',  # Use GPT-4 for more detailed analysis
    result_type=SpecialtyAnalysis,
    # ... rest of configuration
)
```

## Security Notes

- Never commit your API keys to version control
- Keep your `.env` file in `.gitignore`
- Use environment variables for production deployments
- Regularly rotate your API keys

## Next Steps

This analysis system provides the foundation for:
- Integration with Salesforce APIs
- Real-time dashboard development
- Automated reporting systems
- Performance tracking and metrics
- Predictive analytics for outreach effectiveness 