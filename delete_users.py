import sqlite3
import os
import sys
import pickle
from pathlib import Path

def get_db_path():
    """Get the database path based on environment."""
    # For local development, use a local file
    db_path = "techmuse.db"
    print(f"Using development database path: {db_path}")
    return db_path

def get_credentials_path():
    """Get the path to the credentials file."""
    credentials_dir = Path(__file__).parent / "data"
    credentials_path = credentials_dir / "credentials.pkl"
    return credentials_path

def list_users():
    """List all users in the database and file storage."""
    # First check SQLite database
    print("\n=== CHECKING SQLITE DATABASE ===")
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT id, username, email FROM users")
        users = cursor.fetchall()
        
        if not users:
            print("No users found in the SQLite database.")
        else:
            print("\nUsers in SQLite database:")
            print("=" * 80)
            print(f"{'ID':<36} | {'Username':<20} | {'Email':<30}")
            print("-" * 80)
            
            for user in users:
                user_id, username, email = user
                print(f"{user_id:<36} | {username:<20} | {email:<30}")
            
            print("=" * 80)
    except Exception as e:
        print(f"Error listing users from SQLite: {e}")
    finally:
        conn.close()
    
    # Now check file-based storage
    print("\n=== CHECKING FILE-BASED STORAGE ===")
    credentials_path = get_credentials_path()
    
    if not credentials_path.exists():
        print(f"Credentials file not found at: {credentials_path}")
        return
    
    try:
        with open(credentials_path, "rb") as f:
            credentials = pickle.load(f)
        
        if not credentials:
            print("No users found in file-based storage.")
        else:
            print("\nUsers in file-based storage:")
            print("=" * 80)
            print(f"{'Username':<20} | {'Email':<30} | {'Verified':<10}")
            print("-" * 80)
            
            for username, data in credentials.items():
                email = data.get("email", "N/A")
                verified = "Yes" if data.get("is_verified", False) else "No"
                print(f"{username:<20} | {email:<30} | {verified:<10}")
            
            print("=" * 80)
    except Exception as e:
        print(f"Error listing users from file storage: {e}")

def delete_user_by_email(email):
    """Delete a user by their email address from both storage mechanisms."""
    # First try SQLite database
    print("\n=== CHECKING SQLITE DATABASE ===")
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    try:
        # First check if the user exists
        cursor.execute("SELECT username FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        
        if user:
            # Delete the user
            cursor.execute("DELETE FROM users WHERE email = ?", (email,))
            conn.commit()
            print(f"User with email {email} (username: {user[0]}) has been deleted from SQLite database.")
        else:
            print(f"No user found with email {email} in SQLite database.")
    except Exception as e:
        print(f"Error deleting user from SQLite: {e}")
    finally:
        conn.close()
    
    # Now try file-based storage
    print("\n=== CHECKING FILE-BASED STORAGE ===")
    credentials_path = get_credentials_path()
    
    if not credentials_path.exists():
        print(f"Credentials file not found at: {credentials_path}")
        return
    
    try:
        with open(credentials_path, "rb") as f:
            credentials = pickle.load(f)
        
        # Find user by email
        username_to_delete = None
        for username, data in credentials.items():
            if data.get("email") == email:
                username_to_delete = username
                break
        
        if username_to_delete:
            # Delete the user
            del credentials[username_to_delete]
            
            # Save the updated credentials
            with open(credentials_path, "wb") as f:
                pickle.dump(credentials, f)
            
            print(f"User with email {email} (username: {username_to_delete}) has been deleted from file-based storage.")
        else:
            print(f"No user found with email {email} in file-based storage.")
    except Exception as e:
        print(f"Error deleting user from file storage: {e}")

def delete_all_users():
    """Delete all users from both storage mechanisms except admin users."""
    # First handle SQLite database
    print("\n=== PROCESSING SQLITE DATABASE ===")
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    try:
        # Get the admin user (first user in the database)
        cursor.execute("SELECT id FROM users ORDER BY created_at ASC LIMIT 1")
        admin = cursor.fetchone()
        
        if not admin:
            print("No users found in the SQLite database.")
        else:
            # Delete all users except the admin
            cursor.execute("DELETE FROM users WHERE id != ?", (admin[0],))
            deleted_count = cursor.rowcount
            conn.commit()
            
            print(f"Deleted {deleted_count} users from SQLite database. Admin user was preserved.")
    except Exception as e:
        print(f"Error deleting users from SQLite: {e}")
    finally:
        conn.close()
    
    # Now handle file-based storage
    print("\n=== PROCESSING FILE-BASED STORAGE ===")
    credentials_path = get_credentials_path()
    
    if not credentials_path.exists():
        print(f"Credentials file not found at: {credentials_path}")
        return
    
    try:
        with open(credentials_path, "rb") as f:
            credentials = pickle.load(f)
        
        # Keep only the admin user
        admin_users = ["admin"]
        users_to_delete = [username for username in credentials.keys() if username not in admin_users]
        
        for username in users_to_delete:
            del credentials[username]
        
        # Save the updated credentials
        with open(credentials_path, "wb") as f:
            pickle.dump(credentials, f)
        
        print(f"Deleted {len(users_to_delete)} users from file-based storage. Admin users were preserved.")
    except Exception as e:
        print(f"Error deleting users from file storage: {e}")

def main():
    """Main function to handle command line arguments."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python delete_users.py list                - List all users")
        print("  python delete_users.py delete <email>      - Delete user by email")
        print("  python delete_users.py delete-all          - Delete all non-admin users")
        return
    
    command = sys.argv[1].lower()
    
    if command == "list":
        list_users()
    elif command == "delete" and len(sys.argv) >= 3:
        email = sys.argv[2]
        delete_user_by_email(email)
    elif command == "delete-all":
        confirm = input("Are you sure you want to delete all non-admin users? (y/n): ")
        if confirm.lower() == 'y':
            delete_all_users()
        else:
            print("Operation cancelled.")
    else:
        print("Invalid command. Use 'list', 'delete <email>', or 'delete-all'.")

if __name__ == "__main__":
    main()
