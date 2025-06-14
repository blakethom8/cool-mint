from dotenv import load_dotenv
from langfuse.decorators import observe
from langfuse.openai import openai
from pydantic import BaseModel, Field
import os
from pathlib import Path
from langfuse import Langfuse
import logging
import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

"""
First, go to https://langfuse.com and create a free account to get your Langfuse credentials.

Make sure you have set the environment variables in the .env file:
LANGFUSE_SECRET_KEY=your-langfuse-api-secret-here
LANGFUSE_PUBLIC_KEY=your-langfuse-api-key-here
LANGFUSE_HOST=your-langfuse-host-here
"""

print("Current working directory:", os.getcwd())
# Try to load .env from the parent directory (project root)
env_path = Path(__file__).parent.parent / "app/.env"
print("Looking for .env file at:", env_path)
load_dotenv(env_path)

# Debug: Check if API keys are loaded
api_key = os.getenv("OPENAI_API_KEY")
langfuse_public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
langfuse_secret_key = os.getenv("LANGFUSE_SECRET_KEY")
langfuse_host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

print("Environment variables check:")
if api_key:
    print("✓ OpenAI API key found!")
else:
    print("✗ OpenAI API key missing!")
if langfuse_public_key and langfuse_secret_key:
    print("✓ Langfuse credentials found!")
    print(f"  Host: {langfuse_host}")
    print(f"  Public key starts with: {langfuse_public_key[:4]}...")
else:
    print("✗ Langfuse credentials missing!")

try:
    # Initialize Langfuse client
    langfuse = Langfuse()
    print("✓ Langfuse client initialized!")
except Exception as e:
    print(f"✗ Error initializing Langfuse client: {str(e)}")
    raise


def test_langfuse_connection():
    """Simple test to verify Langfuse connection without OpenAI."""
    try:
        # Initialize a new Langfuse client
        langfuse = Langfuse()
        logger.info("Starting Langfuse connection test...")

        # Create a test trace
        trace = langfuse.trace(
            name="test_connection",
            tags=["test", "connection_check"],
            metadata={"test_timestamp": time.time(), "environment": "development"},
        )

        logger.info(f"Created test trace with ID: {trace.id}")

        # Add a simple span
        span = trace.span(name="test_operation")
        logger.info("Performing test operation...")
        time.sleep(1)  # Simulate some work
        span.end(metadata={"test": "successful"}, status="success")

        print(f"\n✓ Test trace created successfully!")
        print(f"  Trace ID: {trace.id}")
        print("  Please check your Langfuse dashboard for this trace.")
        print("  It should appear within a few minutes.")
        print("  You can search for it using the Trace ID above.\n")

        # End the trace
        trace.end(status="success")
        return trace.id

    except Exception as e:
        logger.error(f"Error in Langfuse connection test: {str(e)}")
        raise


def generate_story(topic: str, trace=None) -> str:
    """Generate a story using OpenAI with proper Langfuse tracing."""
    try:
        # Create a span for the OpenAI call if we have a trace
        span = trace.span(name="openai_completion") if trace else None

        logger.info(f"Starting story generation about: {topic}")

        # Use the OpenAI chat completion API
        completion = openai.chat.completions.create(
            model="gpt-3.5-turbo",  # or "gpt-4" if you have access
            messages=[
                {"role": "system", "content": "You are a creative storyteller."},
                {"role": "user", "content": f"Write a short story about: {topic}"},
            ],
            temperature=0.7,
            max_tokens=300,
        )

        # Extract the story from the response
        story = completion.choices[0].message.content

        # Update the span if we have one
        if span:
            span.update(
                status="success",
                metadata={
                    "topic": topic,
                    "model": "gpt-3.5-turbo",
                    "completion_tokens": completion.usage.completion_tokens,
                    "total_tokens": completion.usage.total_tokens,
                },
            )

        logger.info("Successfully generated story")
        return story

    except Exception as e:
        logger.error(f"Error in story generation: {str(e)}")
        if span:
            span.update(status="error", metadata={"error": str(e)})
        raise


def run_story_example():
    """Run the story generation example with proper tracing."""
    try:
        # Create a trace for the entire operation
        trace = langfuse.trace(
            name="story_generation",
            tags=["example", "story"],
            metadata={"version": "1.0"},
        )
        logger.info(f"Starting story generation with trace ID: {trace.id}")

        # Generate the story
        story = generate_story("a robot learning to cook", trace)

        # Print preview and trace info
        print("\n✓ Story generated successfully!")
        print(f"Preview: {story[:100]}...")
        print(f"\nCheck your Langfuse dashboard for trace ID: {trace.id}")

        # Update the trace status
        trace.update(status="success")

    except Exception as e:
        logger.error(f"Error in example run: {str(e)}")
        if "trace" in locals():
            trace.update(status="error", metadata={"error": str(e)})
        raise


if __name__ == "__main__":
    # Uncomment the function you want to run:

    # Test just the Langfuse connection:
    # test_langfuse_connection()

    # Run the story generation example:
    run_story_example()

# Keep the original code but commented out for reference
"""
@observe()
def simple_story_generator(topic: str) -> str:
    try:
        logger.info(f"Starting story generation about: {topic}")
        
        response = openai.responses.create(
            model="gpt-4.1",
            input=[
                {"role": "system", "content": "You are a creative storyteller."},
                {"role": "user", "content": f"Write a short story about: {topic}"},
            ],
        )

        story = response.output_text
        logger.info("Successfully generated story")
        
        return story
    except Exception as e:
        logger.error(f"Error in story generation: {str(e)}")
        raise

def run_simple_example():
    try:
        # Create an explicit trace
        trace = langfuse.trace(name="story_generation")
        logger.info("Starting example run with trace ID: " + trace.id)
        
        story = simple_story_generator("a robot learning to cook")
        print(f"Generated story: {story[:100]}...")
        print(f"Check your LangFuse dashboard to see the tracked call! Trace ID: {trace.id}")
        
        # Add some metadata to the trace
        trace.update(
            tags=["example", "story"],
            metadata={"topic": "robot cooking"}
        )
        trace.end(status="success")
            
    except Exception as e:
        logger.error(f"Error in example run: {str(e)}")
        raise
"""
