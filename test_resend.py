import os
import resend
from dotenv import load_dotenv, find_dotenv

print("Starting Resend API test...")

# Find and load .env file
env_path = find_dotenv()
print(f"Found .env file at: {env_path}")
load_dotenv(env_path)

# Get and check API key
api_key = os.getenv('RESEND_API_KEY', '')
print(f'Raw API key length: {len(api_key)}')
print(f'Raw API key first 4 chars: {api_key[:4] if api_key else "NONE"}')

# Strip whitespace
api_key = api_key.strip()
print(f'Stripped API key length: {len(api_key)}')
print(f'Stripped API key first 4 chars: {api_key[:4] if api_key else "NONE"}')
print(f'Starts with re_: {api_key.startswith("re_")}')

# Set API key in resend module
resend.api_key = api_key
print('API key set in resend module')
print(f'Resend module API key first 4 chars: {resend.api_key[:4] if resend.api_key else "NONE"}')

try:
    # Try to send a test email
    print("\nAttempting to send test email...")
    response = resend.Emails.send({
        'from': 'onboarding@resend.dev',
        'to': 'ctrwillow@gmail.com',
        'subject': 'API Key Test',
        'html': 'Testing API key configuration'
    })
    print(f'Success! Response: {response}')
except Exception as e:
    print(f'\nError occurred:')
    print(f'Error type: {type(e).__name__}')
    print(f'Error message: {str(e)}')
