"""
Simplified web crawler service using FireCrawl for provider website extraction.

This service extracts structured information from healthcare provider websites
using FireCrawl's Pydantic model approach for clean, reliable data extraction.
"""

import logging
import os
from datetime import datetime
from typing import List, Optional
from dataclasses import dataclass
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from pathlib import Path
from firecrawl import FirecrawlApp, JsonConfig

# Configure logging
logger = logging.getLogger(__name__)


# Load environment variables from multiple possible locations
def load_environment_variables():
    """Load environment variables from .env file in multiple possible locations."""
    env_locations = [
        ".env",  # Current directory
        "../.env",  # Parent directory
        "../../.env",  # Root directory
        "../app/.env",  # App directory from playground
        "app/.env",  # App directory from root
        os.path.join(
            os.path.dirname(__file__), "..", "..", ".env"
        ),  # Root from service
        os.path.join(
            os.path.dirname(__file__), "..", ".env"
        ),  # App directory from service
    ]

    env_loaded = False
    for env_path in env_locations:
        if Path(env_path).exists():
            load_dotenv(env_path)
            logger.info(f"✅ Loaded environment variables from {env_path}")
            env_loaded = True
            break

    if not env_loaded:
        logger.warning(
            "⚠️ No .env file found. Trying to use system environment variables."
        )

    return env_loaded


# Load environment variables when module is imported
load_environment_variables()


def get_firecrawl_api_key() -> Optional[str]:
    """Get FireCrawl API key from environment variables."""
    api_key = (
        os.getenv("FIRECRAWL_API_KEY")
        or os.getenv("FIRECRAWL_KEY")
        or os.getenv("FIRE_CRAWL_API_KEY")
    )

    if api_key:
        logger.info("🔥 FireCrawl API key found in environment")
    else:
        logger.warning("⚠️ No FireCrawl API key found in environment variables")
        logger.info("💡 To use FireCrawl, add FIRECRAWL_API_KEY to your .env file")

    return api_key


class ProviderData(BaseModel):
    """Pydantic model for structured provider website data extraction."""

    practice_name: str = Field(
        description="The name of the medical practice, clinic, or healthcare organization"
    )
    providers: List[str] = Field(
        default_factory=list,
        description="List of healthcare providers, doctors, or staff members with their titles/specialties",
    )
    services: List[str] = Field(
        default_factory=list,
        description="List of medical services, treatments, or specialties offered by the practice",
    )
    specialties: List[str] = Field(
        default_factory=list,
        description="Medical specialties of the practice (e.g., Cardiology, Dermatology, Orthopedics, Primary Care, etc.)",
    )
    practice_overview: str = Field(
        default="",
        description="Overview or about us section describing the practice, mission, history, or general information",
    )
    useful_descriptions: List[str] = Field(
        default_factory=list,
        description="Other useful descriptions of the practice, additional information, or relevant content",
    )


@dataclass
class CrawlResult:
    """Simple result container for crawled provider data."""

    url: str
    practice_name: str
    providers: List[str]
    services: List[str]
    specialties: List[str]
    practice_overview: str
    useful_descriptions: List[str]
    raw_content: str
    extraction_timestamp: str

    def __post_init__(self):
        if not self.extraction_timestamp:
            self.extraction_timestamp = datetime.now().isoformat()


class WebCrawlerService:
    """Simplified web crawler service using FireCrawl."""

    def __init__(self, firecrawl_api_key: Optional[str] = None):
        """Initialize the web crawler with FireCrawl."""
        api_key = firecrawl_api_key or get_firecrawl_api_key()

        if not api_key:
            raise ValueError(
                "FireCrawl API key is required. "
                "Set FIRECRAWL_API_KEY in your .env file or pass it directly."
            )

        self.app = FirecrawlApp(api_key=api_key)
        self.json_config = JsonConfig(schema=ProviderData)

        logger.info("🔥 FireCrawl service initialized successfully")

    async def crawl_provider_website(self, url: str) -> Optional[CrawlResult]:
        """
        Crawl a provider website and extract structured information.

        Args:
            url: The provider website URL

        Returns:
            CrawlResult object with extracted information
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        logger.info(f"[{timestamp}] 🚀 Starting FireCrawl extraction for: {url}")

        try:
            # Use FireCrawl to extract structured data
            result = self.app.scrape_url(
                url,
                formats=["json"],
                json_options=self.json_config,
                only_main_content=False,
                timeout=120000,
            )

            # Extract the structured data
            provider_data = result.json

            # Get raw content for LLM processing if needed
            raw_content = str(result.json) if result.json else ""

            # Create result object
            crawl_result = CrawlResult(
                url=url,
                practice_name=provider_data.get("practice_name", ""),
                providers=provider_data.get("providers", []),
                services=provider_data.get("services", []),
                specialties=provider_data.get("specialties", []),
                practice_overview=provider_data.get("practice_overview", ""),
                useful_descriptions=provider_data.get("useful_descriptions", []),
                raw_content=raw_content,
                extraction_timestamp=datetime.now().isoformat(),
            )

            timestamp = datetime.now().strftime("%H:%M:%S")
            logger.info(f"[{timestamp}] ✅ FireCrawl extraction successful for: {url}")
            logger.info(
                f"[{timestamp}] 📊 Extracted: {len(crawl_result.services)} services, {len(crawl_result.providers)} providers, {len(crawl_result.specialties)} specialties"
            )

            return crawl_result

        except Exception as e:
            timestamp = datetime.now().strftime("%H:%M:%S")
            logger.error(f"[{timestamp}] ❌ FireCrawl extraction failed for {url}: {e}")
            return None

    def to_dict(self, crawl_result: CrawlResult) -> dict:
        """Convert CrawlResult to dictionary for serialization."""
        return {
            "url": crawl_result.url,
            "practice_name": crawl_result.practice_name,
            "providers": crawl_result.providers,
            "services": crawl_result.services,
            "specialties": crawl_result.specialties,
            "practice_overview": crawl_result.practice_overview,
            "useful_descriptions": crawl_result.useful_descriptions,
            "raw_content": crawl_result.raw_content,
            "extraction_timestamp": crawl_result.extraction_timestamp,
        }

    def to_llm_context(self, crawl_result: CrawlResult) -> str:
        """
        Convert CrawlResult to formatted string for LLM processing.

        Args:
            crawl_result: The extracted provider data

        Returns:
            Formatted string optimized for LLM consumption
        """
        sections = []

        sections.append(f"**Healthcare Provider: {crawl_result.practice_name}**")
        sections.append(f"URL: {crawl_result.url}")
        sections.append(f"Extracted: {crawl_result.extraction_timestamp}")
        sections.append("")

        if crawl_result.practice_overview:
            sections.append("**Practice Overview:**")
            sections.append(crawl_result.practice_overview)
            sections.append("")

        if crawl_result.specialties:
            sections.append("**Medical Specialties:**")
            for specialty in crawl_result.specialties:
                sections.append(f"• {specialty}")
            sections.append("")

        if crawl_result.services:
            sections.append("**Services Offered:**")
            for service in crawl_result.services:
                sections.append(f"• {service}")
            sections.append("")

        if crawl_result.providers:
            sections.append("**Healthcare Providers:**")
            for provider in crawl_result.providers:
                sections.append(f"• {provider}")
            sections.append("")

        if crawl_result.useful_descriptions:
            sections.append("**Additional Information:**")
            for description in crawl_result.useful_descriptions:
                sections.append(f"• {description}")
            sections.append("")

        return "\n".join(sections)


# Example usage
async def test_crawler():
    """Test function to demonstrate the simplified crawler."""
    try:
        crawler = WebCrawlerService()

        # Test with a healthcare provider website
        test_url = "https://www.mayoclinic.org/about-mayo-clinic"

        result = await crawler.crawl_provider_website(test_url)

        if result:
            print("🎉 Crawl successful!")
            print(f"Practice: {result.practice_name}")
            print(f"Services: {len(result.services)} found")
            print(f"Providers: {len(result.providers)} found")
            print(f"Specialties: {len(result.specialties)} found")
            print(f"Practice Overview: {'Yes' if result.practice_overview else 'None'}")
            print(f"Descriptions: {len(result.useful_descriptions)} found")

            # Convert to LLM-friendly format
            llm_context = crawler.to_llm_context(result)
            print("\n--- LLM Context ---")
            print(llm_context)
        else:
            print("❌ Crawl failed")

    except ValueError as e:
        print(f"❌ Configuration error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(test_crawler())
