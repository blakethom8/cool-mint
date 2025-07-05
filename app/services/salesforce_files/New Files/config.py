import os

def setup_openai_key():
    """
    Setup OpenAI API key for the analysis
    """
    # Check if API key is already set
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        print("🔑 OpenAI API Key Setup Required")
        print("=" * 40)
        print("To run the analysis, you need to set your OpenAI API key.")
        print("\nYou can set it in one of these ways:")
        print("\n1. Environment Variable (Recommended):")
        print("   Windows PowerShell:")
        print("   $env:OPENAI_API_KEY='your_api_key_here'")
        print("\n2. Or create a .env file with:")
        print("   OPENAI_API_KEY=your_api_key_here")
        print("\n3. Get your API key from: https://platform.openai.com/api-keys")
        print("\n⚠️  Important: Keep your API key secure and never commit it to version control!")
        return False
    else:
        print(f"✅ OpenAI API key is configured")
        # Only show first and last 4 characters for security
        masked_key = f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) > 8 else "****"
        print(f"   Key: {masked_key}")
        return True

if __name__ == "__main__":
    setup_openai_key() 