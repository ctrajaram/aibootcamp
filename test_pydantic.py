"""
Test script to demonstrate Pydantic validation in the Technical Blog Generator.

This script shows how Pydantic validates the ResearchTopic model,
handling both valid and invalid inputs.
"""

from app.agents.researcher import ResearchTopic
from pydantic import ValidationError
import json

def print_separator(title):
    """Print a separator with a title."""
    print("\n" + "=" * 50)
    print(f" {title} ".center(50, "="))
    print("=" * 50 + "\n")

def test_valid_input():
    """Test valid inputs for ResearchTopic."""
    print_separator("VALID INPUTS")
    
    # Test case 1: All fields provided
    try:
        topic1 = ResearchTopic(
            title="Docker Containerization",
            keywords=["containers", "virtualization", "microservices"],
            depth="intermediate"
        )
        print("✅ Test case 1 (All fields): Valid")
        print(f"   Title: {topic1.title}")
        print(f"   Keywords: {topic1.keywords}")
        print(f"   Depth: {topic1.depth}")
    except ValidationError as e:
        print(f"❌ Test case 1 failed: {e}")
    
    # Test case 2: Using default depth
    try:
        topic2 = ResearchTopic(
            title="Python Async Programming",
            keywords=["asyncio", "concurrency", "coroutines"]
        )
        print("\n✅ Test case 2 (Default depth): Valid")
        print(f"   Title: {topic2.title}")
        print(f"   Keywords: {topic2.keywords}")
        print(f"   Depth: {topic2.depth} (default value used)")
    except ValidationError as e:
        print(f"❌ Test case 2 failed: {e}")
    
    # Test case 3: Empty keywords list
    try:
        topic3 = ResearchTopic(
            title="Machine Learning Basics",
            keywords=[],
            depth="beginner"
        )
        print("\n✅ Test case 3 (Empty keywords): Valid")
        print(f"   Title: {topic3.title}")
        print(f"   Keywords: {topic3.keywords} (empty list is valid)")
        print(f"   Depth: {topic3.depth}")
    except ValidationError as e:
        print(f"❌ Test case 3 failed: {e}")

def test_invalid_input():
    """Test invalid inputs for ResearchTopic."""
    print_separator("INVALID INPUTS")
    
    # Test case 4: Missing required field (title)
    try:
        topic4 = ResearchTopic(
            keywords=["react", "javascript", "frontend"],
            depth="advanced"
        )
        print("❌ Test case 4 should have failed but didn't")
    except ValidationError as e:
        print("✅ Test case 4 (Missing title): Invalid as expected")
        print(f"   Error: {e}")
    
    # Test case 5: Invalid depth value
    try:
        topic5 = ResearchTopic(
            title="Web Security",
            keywords=["authentication", "encryption"],
            depth="expert"  # Not in allowed values
        )
        print("\n❌ Test case 5 should have failed but didn't")
    except ValidationError as e:
        print("\n✅ Test case 5 (Invalid depth): Invalid as expected")
        print(f"   Error: {e}")
    
    # Test case 6: Wrong data types
    try:
        topic6 = ResearchTopic(
            title=123,  # Should be string
            keywords="databases, sql, nosql",  # Should be list
            depth="intermediate"
        )
        print("\n❌ Test case 6 should have failed but didn't")
    except ValidationError as e:
        print("\n✅ Test case 6 (Wrong data types): Invalid as expected")
        print(f"   Error: {e}")
        
    # Test case 7: Numeric-only title
    try:
        topic7 = ResearchTopic(
            title="12345",
            keywords=["test"],
            depth="intermediate"
        )
        print("\n❌ Test case 7 should have failed but didn't")
    except ValidationError as e:
        print("\n✅ Test case 7 (Numeric-only title): Invalid as expected")
        print(f"   Error: {e}")

def test_from_user_input():
    """Test converting user input to ResearchTopic."""
    print_separator("SIMULATING USER INPUT")
    
    # Simulate user input from Streamlit
    user_topic = "GraphQL API Design"
    user_keywords = "api, rest, queries, mutations"
    user_depth = "advanced"
    
    print("User input:")
    print(f"Topic: {user_topic}")
    print(f"Keywords: {user_keywords}")
    print(f"Depth: {user_depth}")
    
    # Process input as done in the Streamlit app
    try:
        # Convert comma-separated string to list
        keywords_list = [k.strip() for k in user_keywords.split(",") if k.strip()]
        
        # Create ResearchTopic instance
        research_topic = ResearchTopic(
            title=user_topic,
            keywords=keywords_list,
            depth=user_depth
        )
        
        print("\n✅ User input processed successfully")
        print("Validated ResearchTopic:")
        print(json.dumps(research_topic.dict(), indent=2))
    except ValidationError as e:
        print(f"\n❌ User input validation failed: {e}")

if __name__ == "__main__":
    print("\nTESTING PYDANTIC VALIDATION FOR RESEARCH TOPIC MODEL")
    print("This demonstrates how Pydantic validates our data model")
    
    test_valid_input()
    test_invalid_input()
    test_from_user_input()
    
    print("\nTest complete! This shows how Pydantic ensures data integrity.") 