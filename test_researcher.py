import os
from dotenv import load_dotenv
from app.agents.researcher import ResearchTopic, research_topic

# Load environment variables
load_dotenv()

# Check if required API keys are set
openai_api_key = os.getenv("OPENAI_API_KEY")
google_api_key = os.getenv("GOOGLE_API_KEY")
google_cse_id = os.getenv("GOOGLE_CSE_ID")

print(f"OpenAI API Key configured: {'Yes' if openai_api_key else 'No'}")
print(f"Google API Key configured: {'Yes' if google_api_key else 'No'}")
print(f"Google CSE ID configured: {'Yes' if google_cse_id else 'No'}")

if not (openai_api_key and google_api_key and google_cse_id):
    print("Please set all required API keys in your .env file")
    exit(1)

# Test the researcher agent
print("\nTesting researcher agent...")
topic = ResearchTopic(
    title="Python asyncio for beginners",
    keywords=["asyncio", "concurrency", "event loop", "coroutines"],
    depth="beginner"
)

print(f"Researching topic: {topic.title}")
print(f"Keywords: {', '.join(topic.keywords)}")
print(f"Depth: {topic.depth}")

try:
    print("\nGenerating content (this may take a few minutes)...")
    result = research_topic(topic)
    
    if "error" in result:
        print(f"\nResearch failed: {result['error']}")
    else:
        print("\nResearch successful!")
        print("\nContent preview:")
        content = result["content"]
        print(content[:500] + "..." if len(content) > 500 else content)
except Exception as e:
    print(f"\nResearch test failed: {str(e)}") 