import os
from dotenv import load_dotenv
import openai
import sys

# Load environment variables
load_dotenv()

# Get API key
api_key = os.getenv("OPENAI_API_KEY")

print(f"API Key found: {'Yes' if api_key else 'No'}")
print(f"API Key length: {len(api_key) if api_key else 0}")
print(f"First few characters: {api_key[:5]}... (should start with 'sk-')")

# Test the API key
try:
    openai.api_key = api_key
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": "Hello, are you working?"}]
    )
    print("\nAPI TEST SUCCESSFUL!")
    print(f"Response: {response.choices[0].message.content}")
except Exception as e:
    print("\nAPI TEST FAILED!")
    print(f"Error: {str(e)}")

print("\nIf you see an authentication error, check that:")
print("1. Your API key starts with 'sk-'")
print("2. Your API key is not expired")
print("3. Your account has available credits")
print("4. There are no extra spaces or characters in your .env file") 