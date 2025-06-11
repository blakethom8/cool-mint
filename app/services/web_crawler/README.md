# Web Crawler Service

A simplified, AI-powered web crawler service for extracting structured information from healthcare provider websites using FireCrawl's Pydantic model approach.

## 🎯 What This Service Does

This service takes a healthcare provider website URL and extracts exactly **6 structured fields**:

1. **Practice Name** - The name of the medical practice/clinic
2. **Providers** - List of doctors/healthcare staff with titles
3. **Services** - List of medical services offered
4. **Specialties** - Medical specialties (Cardiology, Dermatology, etc.)
5. **Practice Overview** - About us/mission statement content
6. **Useful Descriptions** - Additional relevant information

## 🏗️ Architecture Overview

### Core Components

```
web_crawler/
├── web_crawler_service.py    # Main service file
└── README.md                # This documentation
```

### Key Classes

1. **`ProviderData`** (Pydantic Model)
   - Defines the extraction schema for FireCrawl
   - Uses field descriptions to guide AI extraction

2. **`CrawlResult`** (Dataclass)
   - Clean result container returned to your application
   - Includes extraction timestamp and raw content

3. **`WebCrawlerService`** (Main Service)
   - Handles FireCrawl initialization and API calls
   - Provides helper methods for data conversion

## 🚀 Quick Start

### Basic Usage

```python
from services.web_crawler.web_crawler_service import WebCrawlerService

# Initialize the service (uses FIRECRAWL_API_KEY from .env)
crawler = WebCrawlerService()

# Crawl a website
result = await crawler.crawl_provider_website("https://example-clinic.com")

if result:
    print(f"Practice: {result.practice_name}")
    print(f"Services: {result.services}")
    print(f"Specialties: {result.specialties}")
    print(f"Overview: {result.practice_overview}")
```

### Environment Setup

1. Get API key from [firecrawl.dev](https://firecrawl.dev/)
2. Add to your `.env` file:
   ```
   FIRECRAWL_API_KEY=fc-your-api-key-here
   ```
3. Install dependency: `pip install firecrawl-py`

## 🔧 How to Modify Structured Output

### Adding New Fields

To add a new field to the extraction (e.g., "contact_info"):

1. **Update ProviderData Model** (lines ~70-90):
   ```python
   class ProviderData(BaseModel):
       # ... existing fields ...
       contact_info: Dict[str, str] = Field(
           default_factory=dict,
           description="Contact information including phone, email, address"
       )
   ```

2. **Update CrawlResult Dataclass** (lines ~95-110):
   ```python
   @dataclass
   class CrawlResult:
       # ... existing fields ...
       contact_info: Dict[str, str]
   ```

3. **Update Extraction Logic** (lines ~145-165):
   ```python
   crawl_result = CrawlResult(
       # ... existing fields ...
       contact_info=provider_data.get("contact_info", {}),
   )
   ```

4. **Update Helper Methods**:
   - `to_dict()` method (lines ~175-185)
   - `to_llm_context()` method (lines ~190-220)
   - Logging messages (lines ~170)

### Modifying Field Descriptions

The AI extraction quality depends on field descriptions. To improve extraction:

```python
services: List[str] = Field(
    default_factory=list,
    description="Comprehensive list of medical services, treatments, procedures, and healthcare offerings including primary care, specialty services, diagnostic services, and therapeutic treatments"
)
```

**Tips for better descriptions:**
- Be specific about what you want extracted
- Include examples in parentheses
- Mention synonyms or alternative terms
- Specify the format (list, string, etc.)

## 🎮 Using the Playground Demo

### Location
The demo script is located at: `playground/web_crawler_demo.py`

### Running the Demo

1. **Activate Virtual Environment**:
   ```bash
   source .venv/bin/activate
   ```

2. **Run Demo**:
   ```bash
   cd playground
   python web_crawler_demo.py
   ```

### Demo Features

The playground provides 5 menu options:

#### 1. Show Current Configuration
- Displays API key status (masked for security)
- Shows extraction method being used

#### 2. Demo with Multiple Provider URLs
- Tests 3 different healthcare websites
- Shows extraction summaries for each
- Demonstrates batch processing capability

#### 3. Analyze Single URL in Detail
- Interactive URL input
- Full detailed output
- Saves results to JSON file
- Shows both dictionary and LLM-formatted output

#### 4. Show Data Structure Example
- Displays sample data structure
- Shows expected output format
- Demonstrates both JSON and LLM context formatting

#### 5. Exit
- Clean exit from demo

### Demo Output Formats

The service provides two output formats:

1. **Dictionary Format** (for database storage):
   ```python
   data_dict = crawler.to_dict(result)
   # Returns clean dictionary for JSON serialization
   ```

2. **LLM Context Format** (for AI processing):
   ```python
   llm_text = crawler.to_llm_context(result)
   # Returns formatted markdown-style text
   ```

## 🐛 Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure you're in the virtual environment: `source .venv/bin/activate`
   - Check Python path setup in demo script

2. **API Key Issues**
   - Verify `FIRECRAWL_API_KEY` is set in `.env` file
   - Check API key format (should start with `fc-`)

3. **Extraction Quality Issues**
   - Improve field descriptions in `ProviderData` model
   - Test with different websites
   - Check FireCrawl documentation for advanced options

4. **Timeout Issues**
   - Increase timeout in `scrape_url()` call (currently 120000ms)
   - Some complex websites may take longer to process

## 📊 Data Flow

```
URL Input
    ↓
FireCrawl API (with Pydantic schema)
    ↓
Raw JSON Response
    ↓
CrawlResult Object
    ↓
Dictionary/LLM Format Output
```

## 🔄 Future Enhancements

### Easy Additions
- **Location Extraction**: Add address/phone parsing
- **Insurance Information**: Extract accepted insurance plans
- **Operating Hours**: Parse business hours
- **Review Ratings**: Extract patient ratings/reviews

### Advanced Features
- **Batch Processing**: Process multiple URLs simultaneously
- **Caching**: Cache results to avoid re-crawling
- **Error Retry Logic**: Automatic retries for failed extractions
- **Custom Schemas**: Different schemas for different practice types

## 📝 Code Structure

### File Organization
```python
# Lines 1-50: Imports and environment setup
# Lines 51-70: Environment variable loading
# Lines 71-90: ProviderData Pydantic model
# Lines 91-110: CrawlResult dataclass
# Lines 111-180: WebCrawlerService class
# Lines 181-220: Helper methods (to_dict, to_llm_context)
# Lines 221-260: Test function
```

### Key Methods
- `crawl_provider_website()`: Main extraction method
- `to_dict()`: Convert to dictionary format
- `to_llm_context()`: Convert to LLM-friendly text
- `get_firecrawl_api_key()`: Environment variable helper

## 🔐 Security Considerations

- API keys are masked in logs and demo output
- No sensitive data is stored in raw_content
- Environment variables are loaded securely
- API calls use HTTPS and proper authentication

---

**Last Updated**: January 2024  
**Service Version**: 1.0  
**Dependencies**: `firecrawl-py>=1.4.0`, `pydantic>=2.11.3` 