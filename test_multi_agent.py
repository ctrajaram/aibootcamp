import os
from dotenv import load_dotenv
from app.agents.multi_agent import BlogRequest, generate_blog_post

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

# Test the multi-agent system
print("\nTesting multi-agent blog generation...")
request = BlogRequest(
    topic="Introduction to Docker Containers",
    keywords=["docker", "containers", "virtualization", "devops"],
    depth="beginner"
)

print(f"Topic: {request.topic}")
print(f"Keywords: {', '.join(request.keywords)}")
print(f"Depth: {request.depth}")

try:
    print("\nGenerating blog post (this may take several minutes)...")
    result = generate_blog_post(request)
    
    if "error" in result:
        print(f"\nBlog generation failed: {result['error']}")
    else:
        print("\nBlog generation successful!")
        print("\nContent preview:")
        content = result["content"]
        print(content[:500] + "..." if len(content) > 500 else content)
        
        # Save the full content to a file
        filename = f"{request.topic.lower().replace(' ', '_')}.md"
        with open(filename, "w") as f:
            f.write(content)
        print(f"\nFull content saved to {filename}")
except Exception as e:
    print(f"\nTest failed: {str(e)}") 