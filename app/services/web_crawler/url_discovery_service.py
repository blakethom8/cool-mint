"""
Healthcare Provider URL Discovery Service using FireCrawl Search.

This service searches for healthcare providers based on specialty and location,
returning URLs that can be fed to the web crawler service for detailed scraping.
"""

import logging
import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from pathlib import Path
from firecrawl import FirecrawlApp

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


@dataclass
class SearchResult:
    """Container for individual search result from FireCrawl."""

    title: str
    url: str
    description: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ProviderURLs:
    """Container for discovered healthcare provider URLs."""

    search_query: str
    location: str
    specialty: str
    urls: List[SearchResult]
    total_found: int
    search_timestamp: str

    def __post_init__(self):
        if not self.search_timestamp:
            self.search_timestamp = datetime.now().isoformat()


class HealthcareSearchQuery(BaseModel):
    """Pydantic model for structured healthcare provider search queries."""

    specialty: str = Field(
        description="Medical specialty (e.g., 'interventional cardiologist', 'dermatologist', 'primary care')"
    )
    location: str = Field(
        description="Location including city and state (e.g., 'Torrance, California', 'New York, NY')"
    )
    additional_terms: Optional[List[str]] = Field(
        default_factory=list,
        description="Additional search terms to refine the search (e.g., ['accepting new patients', 'insurance accepted'])",
    )


class URLDiscoveryService:
    """Service for discovering healthcare provider URLs using FireCrawl search."""

    def __init__(self, firecrawl_api_key: Optional[str] = None):
        """Initialize the URL discovery service with FireCrawl."""
        api_key = firecrawl_api_key or get_firecrawl_api_key()

        if not api_key:
            raise ValueError(
                "FireCrawl API key is required. "
                "Set FIRECRAWL_API_KEY in your .env file or pass it directly."
            )

        self.app = FirecrawlApp(api_key=api_key)
        logger.info("🔍 FireCrawl URL Discovery service initialized successfully")

    def build_search_query(
        self,
        specialty: str,
        location: str,
        additional_terms: Optional[List[str]] = None,
    ) -> str:
        """
        Build an optimized search query for healthcare providers.

        Args:
            specialty: Medical specialty to search for
            location: Location (city, state) to search in
            additional_terms: Additional search terms to include

        Returns:
            Optimized search query string
        """
        # Base query with specialty and location
        query_parts = [specialty, "in", location]

        # Add additional terms if provided
        if additional_terms:
            query_parts.extend(additional_terms)

        # Add common healthcare provider terms to improve relevance
        healthcare_terms = ["doctor", "clinic", "medical", "healthcare"]
        query_parts.extend(healthcare_terms)

        return " ".join(query_parts)

    async def discover_provider_urls(
        self,
        specialty: str,
        location: str,
        limit: int = 10,
        additional_terms: Optional[List[str]] = None,
        include_reviews: bool = True,
    ) -> Optional[ProviderURLs]:
        """
        Discover healthcare provider URLs based on specialty and location.

        Args:
            specialty: Medical specialty (e.g., "interventional cardiologist")
            location: Location (e.g., "Torrance, California")
            limit: Maximum number of URLs to return (default: 10)
            additional_terms: Additional search terms to refine results
            include_reviews: Whether to include review sites in filtering

        Returns:
            ProviderURLs object with discovered URLs and metadata
        """
        # Build the search query
        search_query = self.build_search_query(specialty, location, additional_terms)

        timestamp = datetime.now().strftime("%H:%M:%S")
        logger.info(f"[{timestamp}] 🔍 Searching for: {search_query}")

        try:
            # Use FireCrawl search to find provider URLs
            search_result = self.app.search(
                search_query,
                limit=limit,
                lang="en",
                country="us",  # Focus on US results for healthcare providers
            )

            if not search_result or not hasattr(search_result, "data"):
                logger.warning(
                    f"[{timestamp}] ⚠️ No search results returned for: {search_query}"
                )
                return None

            # Process and filter results
            filtered_results = self._filter_healthcare_urls(
                search_result.data, include_reviews
            )

            # Create result object
            provider_urls = ProviderURLs(
                search_query=search_query,
                location=location,
                specialty=specialty,
                urls=filtered_results,
                total_found=len(filtered_results),
                search_timestamp=datetime.now().isoformat(),
            )

            timestamp = datetime.now().strftime("%H:%M:%S")
            logger.info(
                f"[{timestamp}] ✅ Found {len(filtered_results)} provider URLs for {specialty} in {location}"
            )

            return provider_urls

        except Exception as e:
            timestamp = datetime.now().strftime("%H:%M:%S")
            logger.error(
                f"[{timestamp}] ❌ URL discovery failed for {specialty} in {location}: {e}"
            )
            return None

    def _filter_healthcare_urls(
        self, search_results: List[Dict], include_reviews: bool = True
    ) -> List[SearchResult]:
        """
        Filter search results to focus on relevant healthcare provider URLs.

        Args:
            search_results: Raw search results from FireCrawl
            include_reviews: Whether to include review sites

        Returns:
            List of filtered SearchResult objects
        """
        # Healthcare-related domains and patterns
        healthcare_domains = [
            "healthgrades.com",
            "zocdoc.com",
            "vitals.com",
            "webmd.com",
            "doximity.com",
            "ratemds.com",
            "yelp.com",
            "google.com",
            "mayo.edu",
            "clevelandclinic.org",
            "kp.org",
            "sutterhealth.org",
            "cedars-sinai.org",
            "ucla.edu",
            "usc.edu",
            "scripps.org",
        ]

        # Keywords that indicate healthcare provider sites
        healthcare_keywords = [
            "doctor",
            "physician",
            "clinic",
            "medical",
            "health",
            "hospital",
            "cardiology",
            "dermatology",
            "orthopedic",
            "family medicine",
            "internal medicine",
            "pediatric",
            "gynecology",
            "urology",
        ]

        # Review and directory sites (optional inclusion)
        review_domains = [
            "healthgrades.com",
            "zocdoc.com",
            "vitals.com",
            "ratemds.com",
            "yelp.com",
            "google.com",
        ]

        filtered_results = []

        for result in search_results:
            url = result.get("url", "").lower()
            title = result.get("title", "").lower()
            description = result.get("description", "").lower()

            # Skip if it's a review site and reviews are not included
            if not include_reviews and any(domain in url for domain in review_domains):
                continue

            # Check if URL or content contains healthcare-related terms
            is_healthcare_related = (
                any(domain in url for domain in healthcare_domains)
                or any(keyword in title for keyword in healthcare_keywords)
                or any(keyword in description for keyword in healthcare_keywords)
                or any(keyword in url for keyword in healthcare_keywords)
            )

            # Skip obviously non-healthcare URLs
            skip_patterns = [
                "wikipedia.org",
                "facebook.com",
                "twitter.com",
                "linkedin.com",
                "instagram.com",
                "youtube.com",
                "pinterest.com",
                "reddit.com",
                "amazon.com",
                "ebay.com",
                "craigslist.org",
            ]

            if any(pattern in url for pattern in skip_patterns):
                continue

            if is_healthcare_related:
                filtered_results.append(
                    SearchResult(
                        title=result.get("title", ""),
                        url=result.get("url", ""),
                        description=result.get("description", ""),
                        metadata=result.get("metadata"),
                    )
                )

        return filtered_results

    def get_top_urls(self, provider_urls: ProviderURLs, limit: int = 5) -> List[str]:
        """
        Get the top URLs from discovered provider URLs.

        Args:
            provider_urls: ProviderURLs object from discover_provider_urls
            limit: Maximum number of URLs to return

        Returns:
            List of top URLs ready for web scraping
        """
        if not provider_urls or not provider_urls.urls:
            return []

        # Sort by relevance (could be enhanced with scoring algorithm)
        sorted_urls = provider_urls.urls[:limit]

        return [result.url for result in sorted_urls]

    def format_discovery_summary(self, provider_urls: ProviderURLs) -> str:
        """
        Format discovery results into a human-readable summary.

        Args:
            provider_urls: ProviderURLs object from discover_provider_urls

        Returns:
            Formatted summary string
        """
        if not provider_urls:
            return "No provider URLs discovered."

        sections = []
        sections.append(f"🔍 **Healthcare Provider URL Discovery**")
        sections.append(f"**Search Query:** {provider_urls.search_query}")
        sections.append(f"**Specialty:** {provider_urls.specialty}")
        sections.append(f"**Location:** {provider_urls.location}")
        sections.append(f"**Total URLs Found:** {provider_urls.total_found}")
        sections.append(f"**Search Time:** {provider_urls.search_timestamp}")
        sections.append("")

        if provider_urls.urls:
            sections.append("**Discovered Provider URLs:**")
            for i, result in enumerate(provider_urls.urls, 1):
                sections.append(f"**{i}. {result.title}**")
                sections.append(f"   URL: {result.url}")
                sections.append(f"   Description: {result.description}")
                sections.append("")

        return "\n".join(sections)


# Example usage and testing
async def test_url_discovery():
    """Test function to demonstrate the URL discovery service."""
    try:
        discovery_service = URLDiscoveryService()

        # Test search for interventional cardiologist in Torrance, California
        specialty = "interventional cardiologist"
        location = "Torrance, California"

        print(f"🔍 Searching for {specialty} in {location}...")

        provider_urls = await discovery_service.discover_provider_urls(
            specialty=specialty,
            location=location,
            limit=10,
            additional_terms=["accepting new patients"],
        )

        if provider_urls:
            print("🎉 URL discovery successful!")
            print(f"Found {provider_urls.total_found} provider URLs")

            # Get top 5 URLs for scraping
            top_urls = discovery_service.get_top_urls(provider_urls, limit=5)
            print(f"\nTop {len(top_urls)} URLs for scraping:")
            for i, url in enumerate(top_urls, 1):
                print(f"{i}. {url}")

            # Print formatted summary
            print("\n" + "=" * 50)
            print(discovery_service.format_discovery_summary(provider_urls))

            return top_urls
        else:
            print("❌ URL discovery failed")
            return []

    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        return []
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return []


if __name__ == "__main__":
    import asyncio

    asyncio.run(test_url_discovery())
