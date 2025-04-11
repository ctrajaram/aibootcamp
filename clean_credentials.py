import pickle
import os
from pathlib import Path

def get_credentials_path():
    """Get the path to the credentials file."""
    credentials_dir = Path(__file__).parent / "data"
    credentials_path = credentials_dir / "credentials.pkl"
    return credentials_path

def clean_credentials():
    """Keep only techmuse7 user and delete all others."""
    credentials_path = get_credentials_path()
    
    if not credentials_path.exists():
        print(f"Credentials file not found at: {credentials_path}")
        return
    
    try:
        # Load the credentials
        with open(credentials_path, "rb") as f:
            credentials = pickle.load(f)
        
        # Get list of all users
        all_users = list(credentials.keys())
        print(f"Found {len(all_users)} users in credentials.pkl")
        
        # Keep track of users to delete
        users_to_delete = []
        
        # Check if techmuse7 exists
        if "techmuse7" not in credentials:
            print("Warning: User 'techmuse7' not found in credentials.pkl")
            
        # Identify users to delete (all except techmuse7)
        for username in all_users:
            #if username != "techmuse7":
            users_to_delete.append(username)
        
        print(f"Will delete {len(users_to_delete)} users, keeping only 'techmuse7'")
        
        # Confirm deletion
        confirm = input(f"Delete {len(users_to_delete)} users? (y/n): ")
        if confirm.lower() != 'y':
            print("Operation cancelled.")
            return
        
        # Delete the users
        for username in users_to_delete:
            if username in credentials:
                del credentials[username]
                print(f"Deleted user: {username}")
        
        # Save the updated credentials
        with open(credentials_path, "wb") as f:
            pickle.dump(credentials, f)
        
        print(f"Successfully cleaned credentials.pkl, keeping only 'techmuse7'")
        
        # Verify the result
        with open(credentials_path, "rb") as f:
            updated_credentials = pickle.load(f)
        
        print(f"Credentials.pkl now contains {len(updated_credentials)} user(s):")
        for username in updated_credentials:
            print(f"- {username}")
            
    except Exception as e:
        print(f"Error cleaning credentials: {e}")

if __name__ == "__main__":
    clean_credentials()
