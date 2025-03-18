import os
import sys

def test_openai_api():
    """Test if the OpenAI API key is working correctly"""
    try:
        # Get API key from environment
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            # Try to load from .env file
            try:
                from dotenv import load_dotenv
                load_dotenv()
                api_key = os.environ.get("OPENAI_API_KEY")
            except ImportError:
                pass
        
        if not api_key:
            print("ERROR: No OpenAI API key found in environment or .env file.")
            return False
        
        print(f"API Key found (first 5 chars): {api_key[:5]}...")
        
        # Try using the OpenAI API
        try:
            import openai
            client = openai.OpenAI(api_key=api_key)
            
            # Make a simple request
            print("Making a test request to OpenAI API...")
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Say hello world!"}
                ],
                max_tokens=10,
                temperature=0.7
            )
            
            # Check the response
            content = response.choices[0].message.content.strip()
            print(f"Response received: {content}")
            
            print("SUCCESS: OpenAI API test successful!")
            return True
            
        except Exception as e:
            print(f"ERROR using OpenAI API: {str(e)}")
            return False
            
    except Exception as e:
        print(f"UNEXPECTED ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    test_openai_api()
