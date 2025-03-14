import os
from dotenv import load_dotenv
from app.agents.researcher import search_web

# Load environment variables
load_dotenv()

# Check if Google API keys are set
google_api_key = os.getenv("GOOGLE_API_KEY")
google_cse_id = os.getenv("GOOGLE_CSE_ID")

print(f"Google API Key configured: {'Yes' if google_api_key else 'No'}")
print(f"Google CSE ID configured: {'Yes' if google_cse_id else 'No'}")

if not (google_api_key and google_cse_id):
    print("Please set GOOGLE_API_KEY and GOOGLE_CSE_ID in your .env file")
    exit(1)

# Test the search function
print("\nTesting web search functionality...")
query = "Python asyncio best practices"
print(f"Searching for: {query}")

try:
    results = search_web(query)
    print("\nSearch Results:")
    print(results[:500] + "..." if len(results) > 500 else results)
    print("\nSearch test successful!")
except Exception as e:
    print(f"\nSearch test failed: {str(e)}") 