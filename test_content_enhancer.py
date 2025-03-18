import os
from frontend.content_enhancer import ContentEnhancer

def test_paragraph_expansion():
    """Test the paragraph expansion functionality"""
    # Sample paragraph
    test_paragraph = "Machine learning is a subset of artificial intelligence that enables systems to learn from data."
    
    # Initialize the enhancer
    enhancer = ContentEnhancer()
    
    # Test different expansion types
    expansion_types = ["detail", "example", "technical", "simplified", "counterpoint"]
    
    for expansion_type in expansion_types:
        print(f"\n--- {expansion_type.upper()} EXPANSION ---")
        expanded = enhancer.expand_paragraph(test_paragraph, expansion_type)
        print(expanded)
        print("-" * 80)

if __name__ == "__main__":
    # Make sure API key is available
    if not os.environ.get("OPENAI_API_KEY"):
        print("Warning: OPENAI_API_KEY environment variable not set. Using .env file if available.")
        
        # Try to load from .env file
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            print("python-dotenv not installed. Please set OPENAI_API_KEY environment variable manually.")
    
    # Run the test
    test_paragraph_expansion()
