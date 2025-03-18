import os
import sys
from app.content_enhancer import ContentEnhancer
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_content_enhancement():
    """Test the full content enhancement functionality"""
    
    # Sample content with Docker commands section
    test_content = """# Docker Tutorial

## 1. Introduction to Docker
Docker is a platform for developing, shipping, and running applications in containers. Containers allow developers to package an application with all of its dependencies into a standardized unit for software development.

## 2. Docker Basics

### 2.1 Docker Architecture
Docker uses a client-server architecture. The Docker client communicates with the Docker daemon, which builds, runs, and manages Docker containers.

### 2.2 Importance of Docker Commands
Docker provides a set of commands to manage containers and images.

## 3. Conclusion
Docker simplifies the deployment process and ensures consistency across different environments.
"""
    
    # Initialize the enhancer
    try:
        # Make sure API key is available
        if not os.environ.get("OPENAI_API_KEY"):
            print("Warning: OPENAI_API_KEY environment variable not set. Using .env file if available.")
            
            # Try to load from .env file
            try:
                from dotenv import load_dotenv
                load_dotenv()
                if not os.environ.get("OPENAI_API_KEY"):
                    print("ERROR: No OpenAI API key found in environment or .env file.")
                    sys.exit(1)
            except ImportError:
                print("ERROR: python-dotenv not installed and no API key in environment.")
                sys.exit(1)
        
        api_key = os.environ.get("OPENAI_API_KEY")
        print(f"API Key found (first 5 chars): {api_key[:5]}...")
        
        enhancer = ContentEnhancer(api_key=api_key)
        
        # Test different enhancement types
        enhancement_types = ["detail", "example", "technical", "simplified", "counterpoint"]
        
        for enhancement_type in enhancement_types:
            print(f"\n\n{'=' * 80}")
            print(f"TESTING {enhancement_type.upper()} ENHANCEMENT")
            print(f"{'=' * 80}\n")
            
            print("ORIGINAL CONTENT:")
            print("-" * 40)
            print(test_content)
            print("-" * 40)
            
            print("\nENHANCING CONTENT...")
            enhanced = enhancer.enhance_content(test_content, enhancement_type)
            
            print("\nENHANCED CONTENT:")
            print("-" * 40)
            print(enhanced)
            print("-" * 40)
            
            # Check if content was actually enhanced
            if enhanced == test_content:
                print("\n⚠️ WARNING: Enhanced content is identical to original content!")
            else:
                print("\n✅ Content was successfully enhanced!")
                
            # Calculate difference in length
            original_length = len(test_content)
            enhanced_length = len(enhanced)
            diff_percentage = ((enhanced_length - original_length) / original_length) * 100
            
            print(f"\nOriginal length: {original_length} characters")
            print(f"Enhanced length: {enhanced_length} characters")
            print(f"Difference: {enhanced_length - original_length} characters ({diff_percentage:.2f}%)")
            
            input("\nPress Enter to continue to the next enhancement type...")
    
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_content_enhancement()
