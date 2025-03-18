import resend
import os

# Set the API key
api_key = "re_GqtZRXhH_7EFuSJpn3AfU2rvf3KDg5tUp"
resend.api_key = api_key

try:
    # Send a test email
    params = {
        "from": "onboarding@resend.dev",
        "to": "ctrwillow@gmail.com",
        "subject": "Test Email from Resend",
        "html": "<p>This is a test email from Resend.</p>",
    }
    
    print("Sending test email...")
    response = resend.Emails.send(params)
    print(f"Response: {response}")
    
    if response and "id" in response:
        print(f"Email sent successfully with ID: {response['id']}")
    else:
        print(f"Failed to send email: {response}")
        
except Exception as e:
    print(f"Error: {str(e)}")
    print(f"Error type: {type(e).__name__}")
    import traceback
    traceback.print_exc()
