"""
Simplified Web Crawler Demo - Testing FireCrawl provider website extraction.

This script demonstrates how to use the simplified WebCrawlerService to extract
structured information from healthcare provider websites using FireCrawl only.
"""

import asyncio
import sys
import os
from pathlib import Path

# Fix Python path for imports - try multiple approaches
current_dir = Path(__file__).parent
app_dir = current_dir.parent / "app"
root_dir = current_dir.parent

# Add multiple possible paths
possible_paths = [
    str(app_dir),  # Direct path to app directory
    str(root_dir),  # Root directory
    str(current_dir),  # Current directory
]

for path in possible_paths:
    if path not in sys.path:
        sys.path.insert(0, path)

print(f"🔧 Python paths added:")
for path in possible_paths:
    print(f"   - {path}")

from dotenv import load_dotenv
import json


# Load environment variables from multiple possible locations
def load_environment_variables():
    """Load environment variables from .env file in multiple possible locations."""
    env_locations = [
        ".env",  # Current directory (playground)
        "../.env",  # Parent directory (root)
        "../app/.env",  # App directory
        "../../app/.env",  # App directory from deeper nesting
        str(current_dir / ".env"),  # Current directory using Path
        str(root_dir / ".env"),  # Root directory using Path
        str(app_dir / ".env"),  # App directory using Path
    ]

    env_loaded = False
    for env_path in env_locations:
        if Path(env_path).exists():
            load_dotenv(env_path)
            print(f"✅ Loaded environment variables from {env_path}")
            env_loaded = True
            break

    if not env_loaded:
        print("⚠️ No .env file found. Trying to use system environment variables.")
        print("💡 Expected .env file locations:")
        for loc in env_locations:
            abs_path = Path(loc).absolute()
            exists = "✅" if abs_path.exists() else "❌"
            print(f"   {exists} {abs_path}")

    return env_loaded


# Load environment variables when script starts
print("🔧 Loading environment variables...")
load_environment_variables()

# Try importing with better error handling
try:
    from services.web_crawler.web_crawler_service import (
        WebCrawlerService,
        CrawlResult,
        get_firecrawl_api_key,
    )

    print("✅ Successfully imported web crawler service")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("\n🔍 Debugging information:")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Python path entries:")
    for i, path in enumerate(sys.path):
        print(f"   {i}: {path}")

    print(f"\nChecking if service file exists:")
    service_file = app_dir / "services" / "web_crawler" / "web_crawler_service.py"
    print(f"   Service file: {service_file}")
    print(f"   Exists: {service_file.exists()}")

    if service_file.exists():
        print("   File exists but import failed - this might be a dependency issue")
        print("   Try: pip install firecrawl-py")

    sys.exit(1)


def show_configuration():
    """Show the current crawler configuration."""
    print("🔧 Web Crawler Configuration:")
    print("=" * 40)

    api_key = get_firecrawl_api_key()
    if api_key:
        # Only show first 8 characters for security
        masked_key = api_key[:8] + "..." if len(api_key) > 8 else api_key
        print(f"✅ FireCrawl API Key: {masked_key} (loaded from environment)")
        print("   Extraction method: FireCrawl with Pydantic models")
    else:
        print("❌ No FireCrawl API Key found")
        print("   Status: Cannot proceed without API key")
        print("   To use this service, set FIRECRAWL_API_KEY environment variable")

    print()


async def demo_web_crawler():
    """Demonstrate the web crawler with different provider websites."""

    print("🚀 Simplified Web Crawler Demo")
    print("=" * 50)

    try:
        # Initialize the crawler
        crawler = WebCrawlerService()

        # Test URLs for different types of provider websites
        test_urls = [
            "https://www.mayoclinic.org/about-mayo-clinic",
            "https://www.clevelandclinic.org/about",
            "https://www.johnshopkins.org/about",
        ]

        for i, url in enumerate(test_urls, 1):
            print(f"\n📋 Test {i}: Crawling {url}")
            print("-" * 50)

            try:
                # Crawl the website
                result = await crawler.crawl_provider_website(url)

                if result:
                    print(f"✅ Successfully crawled: {result.practice_name}")
                    print(f"📊 Extracted Data Summary:")
                    print(f"   - Practice Name: {result.practice_name}")
                    print(f"   - Services: {len(result.services)} items")
                    print(f"   - Providers: {len(result.providers)} items")
                    print(f"   - Specialties: {len(result.specialties)} items")
                    print(
                        f"   - Practice Overview: {'Yes' if result.practice_overview else 'None'}"
                    )
                    print(f"   - Descriptions: {len(result.useful_descriptions)} items")
                    print(
                        f"   - Raw content length: {len(result.raw_content)} characters"
                    )

                    # Show sample services if any
                    if result.services:
                        print(f"\n🔧 Sample Services:")
                        for service in result.services[:3]:
                            print(f"   • {service}")
                        if len(result.services) > 3:
                            print(f"   ... and {len(result.services) - 3} more")

                    # Show specialties if any
                    if result.specialties:
                        print(f"\n🏥 Medical Specialties:")
                        for specialty in result.specialties[:3]:
                            print(f"   • {specialty}")
                        if len(result.specialties) > 3:
                            print(f"   ... and {len(result.specialties) - 3} more")

                    # Show practice overview if available
                    if result.practice_overview:
                        print(f"\n📋 Practice Overview:")
                        # Truncate long overview
                        short_overview = (
                            result.practice_overview[:200] + "..."
                            if len(result.practice_overview) > 200
                            else result.practice_overview
                        )
                        print(f"   {short_overview}")

                    # Show sample providers if any
                    if result.providers:
                        print(f"\n👨‍⚕️ Sample Providers:")
                        for provider in result.providers[:3]:
                            print(f"   • {provider}")
                        if len(result.providers) > 3:
                            print(f"   ... and {len(result.providers) - 3} more")

                    # Show sample descriptions if any
                    if result.useful_descriptions:
                        print(f"\n📄 Sample Descriptions:")
                        for desc in result.useful_descriptions[:2]:
                            # Truncate long descriptions
                            short_desc = desc[:100] + "..." if len(desc) > 100 else desc
                            print(f"   • {short_desc}")
                        if len(result.useful_descriptions) > 2:
                            print(
                                f"   ... and {len(result.useful_descriptions) - 2} more"
                            )

                    # Convert to LLM context
                    llm_context = crawler.to_llm_context(result)
                    print(f"\n🤖 LLM Context Preview (first 300 chars):")
                    print(f"   {llm_context[:300]}...")

                    # Convert to dictionary for storage
                    data_dict = crawler.to_dict(result)
                    print(f"\n💾 Data ready for storage/database insertion")

                else:
                    print(f"❌ Failed to crawl: {url}")

            except Exception as e:
                print(f"❌ Error crawling {url}: {e}")

            print("\n" + "=" * 50)

    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("💡 Make sure FIRECRAWL_API_KEY is set in your .env file")


async def demo_single_url():
    """Demo with a single URL for detailed analysis."""

    print("\n🔍 Single URL Deep Analysis Demo")
    print("=" * 50)

    # You can change this URL to test with different provider websites
    test_url = input(
        "Enter a provider website URL (or press Enter for default): "
    ).strip()
    if not test_url:
        test_url = "https://www.gynla.com/"

    print(f"\n🎯 Analyzing: {test_url}")

    try:
        crawler = WebCrawlerService()

        result = await crawler.crawl_provider_website(test_url)

        if result:
            print(f"\n✅ Analysis Complete!")
            print(f"Practice Name: {result.practice_name}")
            print(f"URL: {result.url}")
            print(f"Extraction Time: {result.extraction_timestamp}")

            # Full LLM context
            llm_context = crawler.to_llm_context(result)
            print(f"\n📄 Full LLM Context:")
            print(llm_context)

            # Save to file for inspection
            output_file = f"crawler_output_{int(asyncio.get_event_loop().time())}.json"
            data_dict = crawler.to_dict(result)

            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(data_dict, f, indent=2, ensure_ascii=False)

            print(f"\n💾 Full data saved to: {output_file}")

        else:
            print(f"❌ Failed to analyze: {test_url}")

    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("💡 Make sure FIRECRAWL_API_KEY is set in your .env file")
    except Exception as e:
        print(f"❌ Error: {e}")


def demo_data_structure():
    """Show the simplified data structure that will be extracted."""

    print("\n📊 Simplified Data Structure Demo")
    print("=" * 50)

    # Create a sample data structure
    sample_data = CrawlResult(
        url="https://example-clinic.com",
        practice_name="Example Medical Center",
        providers=[
            "Dr. John Smith - Chief of Cardiology",
            "Dr. Sarah Johnson - Emergency Medicine",
            "Dr. Michael Brown - Orthopedic Surgery",
        ],
        services=[
            "Primary Care",
            "Cardiology Services",
            "Emergency Medicine",
            "Orthopedic Surgery",
            "Preventive Care",
        ],
        specialties=[
            "Cardiology",
            "Emergency Medicine",
            "Orthopedic Surgery",
            "Primary Care",
        ],
        practice_overview="We are a comprehensive healthcare facility providing quality medical care to our community. Established in 1985, our mission is to deliver compassionate, innovative healthcare services with a focus on patient-centered care and clinical excellence.",
        useful_descriptions=[
            "Board-certified physicians with over 100 years of combined experience",
            "State-of-the-art medical equipment and facilities",
            "We accept most major insurance plans",
        ],
        raw_content='{"practice_name": "Example Medical Center", "providers": [...], "services": [...]}',
        extraction_timestamp="2024-01-15T10:30:00",
    )

    print("🏗️  Simplified Data Structure Overview:")
    print(f"   • Practice Name: {sample_data.practice_name}")
    print(f"   • Providers: {len(sample_data.providers)} items")
    print(f"   • Services: {len(sample_data.services)} items")
    print(f"   • Specialties: {len(sample_data.specialties)} items")
    print(
        f"   • Practice Overview: {'Yes' if sample_data.practice_overview else 'None'}"
    )
    print(f"   • Descriptions: {len(sample_data.useful_descriptions)} items")

    # Show JSON representation
    try:
        crawler = WebCrawlerService()
        data_dict = crawler.to_dict(sample_data)

        print(f"\n📋 JSON Structure Preview:")
        print(json.dumps(data_dict, indent=2)[:500] + "...")

        # Show LLM context format
        llm_context = crawler.to_llm_context(sample_data)
        print(f"\n🤖 LLM Context Format:")
        print(llm_context)

    except ValueError as e:
        print(f"❌ Cannot initialize crawler: {e}")
        print("💡 This demo requires FIRECRAWL_API_KEY to be set")


async def main():
    """Main demo function with menu."""

    while True:
        print("\n🔥 Simplified Web Crawler Demo Menu")
        print("=" * 40)
        print("1. Show current configuration")
        print("2. Demo with multiple provider URLs")
        print("3. Analyze single URL in detail")
        print("4. Show data structure example")
        print("5. Exit")

        choice = input("\nSelect option (1-5): ").strip()

        if choice == "1":
            show_configuration()
        elif choice == "2":
            await demo_web_crawler()
        elif choice == "3":
            await demo_single_url()
        elif choice == "4":
            demo_data_structure()
        elif choice == "5":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please select 1-5.")


if __name__ == "__main__":
    print("🔥 Simplified Web Crawler Demo Starting...")
    print("This demo uses FireCrawl with Pydantic models for structured extraction")
    print()

    # Show initial configuration
    show_configuration()

    print("💡 Setup Instructions:")
    print("   1. Get API key from https://firecrawl.dev/")
    print("   2. Add FIRECRAWL_API_KEY=your_key_here to your .env file")
    print("   3. Restart this demo")
    print()

    try:
        # Check if we're in IPython/Jupyter
        try:
            import IPython

            if IPython.get_ipython() is not None:
                # We're in IPython/Jupyter - use nest_asyncio
                import nest_asyncio

                nest_asyncio.apply()
                asyncio.get_event_loop().run_until_complete(main())
            else:
                # Regular Python environment
                asyncio.run(main())
        except ImportError:
            # Not in IPython - use regular asyncio.run()
            asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Demo interrupted. Goodbye!")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
