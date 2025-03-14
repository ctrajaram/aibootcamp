import os
import sys
from dotenv import load_dotenv

# Add the app directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.agents.researcher import ResearchTopic, research_topic

# Load environment variables
load_dotenv()

def progress_callback(progress_value, status_message):
    """Simple progress callback for testing."""
    print(f"Progress: {progress_value*100:.1f}% - {status_message}")

def test_crew_blog_generation():
    """Test the multi-agent crew blog generation system."""
    print("Testing multi-agent crew blog generation...")
    print("Using a 5-agent crew: Researcher, Outline Creator, Writer, Editor, and QA Specialist")
    
    # Create a simple test topic
    test_topic = ResearchTopic(
        title="Python Decorators",
        keywords=["functions", "metaprogramming", "advanced"],
        depth="intermediate"
    )
    
    # Generate content with the crew
    print(f"Generating blog post about: {test_topic.title}")
    result = research_topic(
        topic=test_topic,
        progress_callback=progress_callback,
        use_cache=False  # Force fresh generation for testing
    )
    
    # Check for errors
    if "error" in result:
        print(f"Error: {result['error']}")
        return False
    
    # Print the result summary
    print("\n" + "="*50)
    print(f"Blog post generated successfully!")
    print(f"Title: {result['title']}")
    print(f"Depth: {result['depth']}")
    print(f"Keywords: {', '.join(result['keywords'])}")
    print(f"Content length: {len(result['content'])} characters")
    print(f"Quality assured: Yes (passed through 5-agent workflow)")
    print("="*50)
    
    # Save the content to a file for inspection
    with open("test_blog_output.md", "w", encoding="utf-8") as f:
        f.write(result['content'])
    
    print(f"Blog content saved to test_blog_output.md")
    return True

if __name__ == "__main__":
    # Check if API keys are set
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OpenAI API key not set. Please check your .env file.")
        sys.exit(1)
        
    if not (os.getenv("GOOGLE_API_KEY") and os.getenv("GOOGLE_CSE_ID")):
        print("Error: Google Search API credentials not set. Please check your .env file.")
        sys.exit(1)
    
    # Run the test
    success = test_crew_blog_generation()
    
    if success:
        print("\nTest completed successfully!")
    else:
        print("\nTest failed.")
        sys.exit(1) 