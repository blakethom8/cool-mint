"""
Healthcare Provider Discovery Orchestrator - Notebook Version.

This version is optimized for use in Jupyter notebooks and interactive environments.
It handles imports more flexibly and provides a simpler interface.
"""

import logging
import asyncio
import sys
import os
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime

# Set up paths (using the working logic from notebook_code.py)
print("🔧 Setting up paths...")
current_dir = os.getcwd()
print(f"Current working directory: {current_dir}")

# Try to find the project root
possible_roots = [
    current_dir,
    os.path.join(current_dir, "spearmint"),
    "/Users/blakethomson/Documents/Repo/spearmint",
    os.path.abspath(os.path.join(current_dir, "..")),
    os.path.abspath(os.path.join(current_dir, "../..")),
]

project_root = None
for root in possible_roots:
    web_crawler_path = os.path.join(root, "app", "services", "web_crawler")
    if os.path.exists(web_crawler_path):
        project_root = root
        print(f"✅ Found project root: {project_root}")
        break

if not project_root:
    print(
        "❌ Could not find project root. Please run this from the spearmint directory."
    )
    print(f"Tried: {possible_roots}")
else:
    # Add to Python path
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    web_crawler_dir = os.path.join(project_root, "app", "services", "web_crawler")
    if web_crawler_dir not in sys.path:
        sys.path.insert(0, web_crawler_dir)

    print(f"✅ Added paths to sys.path")

# Now try imports with better error handling
try:
    # Try absolute imports (for notebook use)
    from app.services.web_crawler.url_discovery_service import (
        URLDiscoveryService,
        ProviderURLs,
    )
    from app.services.web_crawler.web_crawler_service import (
        WebCrawlerService,
        CrawlResult,
    )

    print("✅ Successfully imported using absolute imports")
except ImportError as e1:
    print(f"❌ Absolute imports failed: {e1}")
    try:
        # Try direct imports from web_crawler directory
        from url_discovery_service import URLDiscoveryService, ProviderURLs
        from web_crawler_service import WebCrawlerService, CrawlResult

        print("✅ Successfully imported using direct imports")
    except ImportError as e2:
        print(f"❌ Direct imports failed: {e2}")

        # Check if files exist
        if project_root:
            web_crawler_dir = os.path.join(
                project_root, "app", "services", "web_crawler"
            )
            url_service_path = os.path.join(web_crawler_dir, "url_discovery_service.py")
            crawler_service_path = os.path.join(
                web_crawler_dir, "web_crawler_service.py"
            )

            print(f"URL service exists: {os.path.exists(url_service_path)}")
            print(f"Crawler service exists: {os.path.exists(crawler_service_path)}")
            print(
                f"Files in web_crawler dir: {os.listdir(web_crawler_dir) if os.path.exists(web_crawler_dir) else 'Directory not found'}"
            )

        raise ImportError(
            f"Could not import required modules. Absolute import error: {e1}. Direct import error: {e2}"
        )

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class ProviderDiscoveryResult:
    """Complete result from healthcare provider discovery and extraction."""

    search_query: str
    specialty: str
    location: str
    discovery_timestamp: str

    # URL Discovery Results
    urls_discovered: int
    discovered_urls: List[str]

    # Web Crawling Results
    urls_crawled: int
    crawl_results: List[CrawlResult]
    failed_crawls: List[str]

    def __post_init__(self):
        if not self.discovery_timestamp:
            self.discovery_timestamp = datetime.now().isoformat()


class HealthcareDiscoveryOrchestrator:
    """Orchestrates URL discovery and web crawling for healthcare providers."""

    def __init__(self, firecrawl_api_key: Optional[str] = None):
        """Initialize the orchestrator with both services."""
        self.url_discovery = URLDiscoveryService(firecrawl_api_key)
        self.web_crawler = WebCrawlerService(firecrawl_api_key)

        logger.info("🚀 Healthcare Discovery Orchestrator initialized successfully")

    async def discover_and_extract_providers(
        self,
        specialty: str,
        location: str,
        max_urls_to_discover: int = 10,
        max_urls_to_crawl: int = 5,
        additional_search_terms: Optional[List[str]] = None,
        include_review_sites: bool = True,
    ) -> Optional[ProviderDiscoveryResult]:
        """
        Complete workflow: discover URLs and extract provider information.

        Args:
            specialty: Medical specialty to search for
            location: Location to search in
            max_urls_to_discover: Maximum URLs to discover (default: 10)
            max_urls_to_crawl: Maximum URLs to crawl (default: 5)
            additional_search_terms: Additional search terms
            include_review_sites: Whether to include review sites

        Returns:
            ProviderDiscoveryResult with complete results
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        logger.info(
            f"[{timestamp}] 🚀 Starting healthcare provider discovery for {specialty} in {location}"
        )

        try:
            # Step 1: Discover URLs
            logger.info(f"[{timestamp}] 🔍 Phase 1: Discovering provider URLs...")
            provider_urls = await self.url_discovery.discover_provider_urls(
                specialty=specialty,
                location=location,
                limit=max_urls_to_discover,
                additional_terms=additional_search_terms,
                include_reviews=include_review_sites,
            )

            if not provider_urls or not provider_urls.urls:
                logger.warning(
                    f"[{timestamp}] ⚠️ No URLs discovered for {specialty} in {location}"
                )
                return None

            # Get top URLs for crawling
            urls_to_crawl = self.url_discovery.get_top_urls(
                provider_urls, limit=max_urls_to_crawl
            )

            timestamp = datetime.now().strftime("%H:%M:%S")
            logger.info(
                f"[{timestamp}] ✅ Phase 1 complete: {len(urls_to_crawl)} URLs selected for crawling"
            )

            # Step 2: Crawl and extract data
            logger.info(f"[{timestamp}] 🌐 Phase 2: Crawling provider websites...")
            crawl_results = []
            failed_crawls = []

            for i, url in enumerate(urls_to_crawl, 1):
                timestamp = datetime.now().strftime("%H:%M:%S")
                logger.info(
                    f"[{timestamp}] 🌐 Crawling {i}/{len(urls_to_crawl)}: {url}"
                )

                crawl_result = await self.web_crawler.crawl_provider_website(url)

                if crawl_result:
                    crawl_results.append(crawl_result)
                    logger.info(f"[{timestamp}] ✅ Successfully crawled: {url}")
                else:
                    failed_crawls.append(url)
                    logger.warning(f"[{timestamp}] ❌ Failed to crawl: {url}")

            # Step 3: Create final result
            discovery_result = ProviderDiscoveryResult(
                search_query=provider_urls.search_query,
                specialty=specialty,
                location=location,
                discovery_timestamp=datetime.now().isoformat(),
                urls_discovered=len(provider_urls.urls),
                discovered_urls=[result.url for result in provider_urls.urls],
                urls_crawled=len(crawl_results),
                crawl_results=crawl_results,
                failed_crawls=failed_crawls,
            )

            timestamp = datetime.now().strftime("%H:%M:%S")
            logger.info(
                f"[{timestamp}] 🎉 Discovery complete: {len(crawl_results)} providers extracted from {len(urls_to_crawl)} URLs"
            )

            return discovery_result

        except Exception as e:
            timestamp = datetime.now().strftime("%H:%M:%S")
            logger.error(f"[{timestamp}] ❌ Healthcare provider discovery failed: {e}")
            return None

    def format_complete_results(self, discovery_result: ProviderDiscoveryResult) -> str:
        """Format complete discovery and extraction results."""
        if not discovery_result:
            return "No provider discovery results available."

        sections = []

        # Header
        sections.append("🏥 **HEALTHCARE PROVIDER DISCOVERY & EXTRACTION REPORT**")
        sections.append("=" * 60)
        sections.append("")

        # Search Summary
        sections.append("📋 **SEARCH SUMMARY**")
        sections.append(f"• **Specialty:** {discovery_result.specialty}")
        sections.append(f"• **Location:** {discovery_result.location}")
        sections.append(f"• **Search Query:** {discovery_result.search_query}")
        sections.append(f"• **Discovery Time:** {discovery_result.discovery_timestamp}")
        sections.append("")

        # Discovery Statistics
        sections.append("📊 **DISCOVERY STATISTICS**")
        sections.append(f"• **URLs Discovered:** {discovery_result.urls_discovered}")
        sections.append(f"• **URLs Crawled:** {discovery_result.urls_crawled}")
        sections.append(
            f"• **Successful Extractions:** {len(discovery_result.crawl_results)}"
        )
        sections.append(f"• **Failed Crawls:** {len(discovery_result.failed_crawls)}")
        sections.append("")

        # Extracted Provider Details
        if discovery_result.crawl_results:
            sections.append("🏥 **EXTRACTED PROVIDER INFORMATION**")
            sections.append("")

            for i, result in enumerate(discovery_result.crawl_results, 1):
                sections.append(
                    f"**{i}. {result.practice_name or 'Unknown Practice'}**"
                )
                sections.append(f"   📍 **URL:** {result.url}")

                if result.specialties:
                    sections.append(
                        f"   🏥 **Specialties:** {', '.join(result.specialties[:3])}"
                    )

                if result.services:
                    sections.append(
                        f"   🩺 **Services:** {', '.join(result.services[:3])}"
                    )
                    if len(result.services) > 3:
                        sections.append(
                            f"      (and {len(result.services) - 3} more services)"
                        )

                if result.providers:
                    sections.append(
                        f"   👨‍⚕️ **Providers:** {', '.join(result.providers[:2])}"
                    )
                    if len(result.providers) > 2:
                        sections.append(
                            f"      (and {len(result.providers) - 2} more providers)"
                        )

                if result.practice_overview:
                    overview = (
                        result.practice_overview[:100] + "..."
                        if len(result.practice_overview) > 100
                        else result.practice_overview
                    )
                    sections.append(f"   📝 **Overview:** {overview}")

                sections.append("")

        return "\n".join(sections)

    def get_structured_results(
        self, discovery_result: ProviderDiscoveryResult
    ) -> Dict[str, Any]:
        """Get structured results as dictionary for API/JSON output."""
        if not discovery_result:
            return {"error": "No discovery results available"}

        providers = []
        for result in discovery_result.crawl_results:
            provider_data = {
                "practice_name": result.practice_name,
                "url": result.url,
                "specialties": result.specialties,
                "services": result.services,
                "providers": result.providers,
                "practice_overview": result.practice_overview,
                "useful_descriptions": result.useful_descriptions,
                "extraction_timestamp": result.extraction_timestamp,
            }
            providers.append(provider_data)

        return {
            "search_summary": {
                "specialty": discovery_result.specialty,
                "location": discovery_result.location,
                "search_query": discovery_result.search_query,
                "discovery_timestamp": discovery_result.discovery_timestamp,
            },
            "statistics": {
                "urls_discovered": discovery_result.urls_discovered,
                "urls_crawled": discovery_result.urls_crawled,
                "successful_extractions": len(discovery_result.crawl_results),
                "failed_crawls": len(discovery_result.failed_crawls),
            },
            "providers": providers,
            "failed_urls": discovery_result.failed_crawls,
            "all_discovered_urls": discovery_result.discovered_urls,
        }


# Quick function for easy notebook use
async def discover_healthcare_providers(
    specialty: str,
    location: str,
    max_urls_to_discover: int = 10,
    max_urls_to_crawl: int = 5,
    firecrawl_api_key: Optional[str] = None,
) -> Optional[ProviderDiscoveryResult]:
    """
    Quick function for healthcare provider discovery in notebooks.

    Args:
        specialty: Medical specialty (e.g., "cardiologist")
        location: Location (e.g., "Los Angeles, CA")
        max_urls_to_discover: Maximum URLs to find (default: 10)
        max_urls_to_crawl: Maximum URLs to scrape (default: 5)
        firecrawl_api_key: Optional API key (uses env var if not provided)

    Returns:
        ProviderDiscoveryResult with complete results
    """
    orchestrator = HealthcareDiscoveryOrchestrator(firecrawl_api_key)
    return await orchestrator.discover_and_extract_providers(
        specialty=specialty,
        location=location,
        max_urls_to_discover=max_urls_to_discover,
        max_urls_to_crawl=max_urls_to_crawl,
    )


# Helper function for notebook use
def run_discovery(
    specialty: str,
    location: str,
    max_urls_to_discover: int = 10,
    max_urls_to_crawl: int = 5,
    firecrawl_api_key: Optional[str] = None,
) -> Optional[ProviderDiscoveryResult]:
    """
    Synchronous wrapper for discover_healthcare_providers that handles the event loop.
    This is the recommended way to run the discovery in notebooks.
    """
    try:
        # Check if we're in IPython/Jupyter
        import IPython

        if IPython.get_ipython() is not None:
            # We're in IPython/Jupyter - use nest_asyncio
            import nest_asyncio

            nest_asyncio.apply()
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(
                discover_healthcare_providers(
                    specialty=specialty,
                    location=location,
                    max_urls_to_discover=max_urls_to_discover,
                    max_urls_to_crawl=max_urls_to_crawl,
                    firecrawl_api_key=firecrawl_api_key,
                )
            )
    except ImportError:
        # Not in IPython - use regular asyncio.run()
        return asyncio.run(
            discover_healthcare_providers(
                specialty=specialty,
                location=location,
                max_urls_to_discover=max_urls_to_discover,
                max_urls_to_crawl=max_urls_to_crawl,
                firecrawl_api_key=firecrawl_api_key,
            )
        )


# Example usage for notebooks
if __name__ == "__main__":
    # This can be run directly or imported into a notebook
    result = run_discovery(
        "gastroenterology",
        "Santa Monica, California",
        max_urls_to_discover=5,
        max_urls_to_crawl=3,
    )

    if result:
        orchestrator = HealthcareDiscoveryOrchestrator()
        print(orchestrator.format_complete_results(result))
