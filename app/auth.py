import streamlit as st
import os
from pathlib import Path
import pickle
import hashlib
import sqlite3
import uuid
import datetime
from datetime import datetime, timedelta
import time
import json
import re
try:
    import bcrypt
except ImportError:
    print("WARNING: bcrypt module not found. Password hashing will use a fallback method.")
    bcrypt = None
import secrets
import string
import requests
import resend
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get credentials - prioritize Streamlit secrets
def get_credentials():
    # First try Streamlit secrets
    try:
        admin_username = st.secrets["ADMIN_USERNAME"]
        admin_password = st.secrets["ADMIN_PASSWORD"]
        return admin_username, admin_password
    except (KeyError, TypeError):
        # Fall back to environment variables
        admin_username = os.getenv("ADMIN_USERNAME", "default_username")
        admin_password = os.getenv("ADMIN_PASSWORD", "default_password")
        return admin_username, admin_password

# Get the credentials
ADMIN_USERNAME, ADMIN_PASSWORD = get_credentials()

# Get Mailgun API key
def get_mailgun_api_key():
    try:
        return st.secrets["MAILGUN_API_KEY"]
    except (KeyError, TypeError):
        return os.getenv("MAILGUN_API_KEY", "")

# Get email sender
def get_email_sender():
    try:
        return st.secrets["MAILGUN_FROM_EMAIL"]
    except (KeyError, TypeError):
        return os.getenv("MAILGUN_FROM_EMAIL", "noreply@techmuse.com")

# Database setup
def get_db_path():
    """Get the database path based on environment."""
    # Check for deployment environment
    is_deployment = False
    
    # Check environment variables
    if os.getenv("DEPLOYMENT", "").lower() == "true":
        is_deployment = True
    elif os.getenv("STREAMLIT_DEPLOYMENT", "0") == "1":
        is_deployment = True
    elif os.getenv("STREAMLIT_SHARING", ""):
        is_deployment = True
    elif os.getenv("STREAMLIT_CLOUD", ""):
        is_deployment = True
    
    # Check Streamlit secrets
    if hasattr(st, "secrets") and "DEPLOYMENT" in st.secrets:
        is_deployment = st.secrets["DEPLOYMENT"].lower() == "true"
    
    # Determine the path based on environment
    if is_deployment:
        # In Streamlit Cloud, use a path in the home directory
        home_dir = os.path.expanduser("~")
        db_dir = os.path.join(home_dir, ".streamlit")
        os.makedirs(db_dir, exist_ok=True)
        db_path = os.path.join(db_dir, "techmuse.db")
        print(f"Using deployment database path: {db_path}")
        return db_path
    else:
        # In development, use a local file
        db_path = "techmuse.db"
        print(f"Using development database path: {db_path}")
        return db_path

def init_db():
    """Initialize the database with required tables."""
    try:
        # Get database path
        db_path = get_db_path()
        print(f"Initializing database at: {db_path}")
        
        # Ensure directory exists
        db_dir = os.path.dirname(db_path)
        if db_dir:  # Only create directory if path has a directory component
            os.makedirs(db_dir, exist_ok=True)
            print(f"Ensured database directory exists: {db_dir}")
        
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("Creating users table if it doesn't exist")
        # Create users table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            created_at TEXT NOT NULL,
            last_login TEXT,
            is_verified INTEGER DEFAULT 0,
            verification_token TEXT,
            verification_expiry TEXT
        )
        ''')
        
        conn.commit()
        
        # Check if admin user exists, create if not
        print(f"Checking if admin user exists: {ADMIN_USERNAME}")
        cursor.execute("SELECT * FROM users WHERE username = ?", (ADMIN_USERNAME,))
        if cursor.fetchone() is None and ADMIN_USERNAME != "default_username":
            # Create admin user
            admin_id = str(uuid.uuid4())
            now = datetime.now().isoformat()
            hashed_password = hashlib.sha256(ADMIN_PASSWORD.encode()).hexdigest()
            
            print(f"Creating admin user: {ADMIN_USERNAME}")
            cursor.execute('''
            INSERT INTO users (id, username, password, name, email, created_at, is_verified)
            VALUES (?, ?, ?, ?, ?, ?, 1)
            ''', (admin_id, ADMIN_USERNAME, hashed_password, "Administrator", "admin@example.com", now))
            
            conn.commit()
            print(f"Admin user created successfully: {ADMIN_USERNAME}")
        
        conn.close()
        print("Database initialization completed successfully")
        return True
    except Exception as e:
        print(f"Error in init_db: {e}")
        import traceback
        traceback.print_exc()
        return False

# Initialize the database
init_db()

class SimpleAuthenticator:
    def __init__(self):
        """Initialize the authenticator with credentials from database or file."""
        # Check if we're in deployment mode
        self.is_deployment = os.getenv("DEPLOYMENT", "false").lower() == "true"
        if hasattr(st, "secrets") and "DEPLOYMENT" in st.secrets:
            self.is_deployment = st.secrets["DEPLOYMENT"].lower() == "true"
        
        # Get admin credentials
        self.admin_username = os.getenv("ADMIN_USERNAME", "")
        self.admin_password = os.getenv("ADMIN_PASSWORD", "")
        
        if hasattr(st, "secrets"):
            if not self.admin_username and "ADMIN_USERNAME" in st.secrets:
                self.admin_username = st.secrets["ADMIN_USERNAME"]
            if not self.admin_password and "ADMIN_PASSWORD" in st.secrets:
                self.admin_password = st.secrets["ADMIN_PASSWORD"]
        
        # Initialize Resend API key from environment or secrets
        try:
            # Try to get API key from environment or Streamlit secrets
            resend_api_key = os.getenv("RESEND_API_KEY", "")
            if not resend_api_key and hasattr(st, "secrets"):
                resend_api_key = st.secrets.get("RESEND_API_KEY", "")
            
            # Set the API key if available
            if resend_api_key:
                resend.api_key = resend_api_key
                print("Resend API key configured successfully")
            else:
                print("WARNING: Resend API key not found in environment or secrets")
        except Exception as e:
            print(f"Error initializing Resend API key: {e}")
        
        if self.is_deployment:
            # In deployment mode, use SQLite database
            self._init_db_if_needed()
            self.credentials = {}  # Not used in deployment mode
        else:
            # In development mode, use file-based credentials
            self.credentials_dir = Path(__file__).parent.parent / "data"
            self.credentials_dir.mkdir(exist_ok=True)
            self.credentials_path = self.credentials_dir / "credentials.pkl"
            
            if self.credentials_path.exists():
                with open(self.credentials_path, "rb") as f:
                    self.credentials = pickle.load(f)
            else:
                # Create default admin user
                self.credentials = {
                    "admin": {
                        "name": "Admin User",
                        "password": self.hash_password("password"),
                        "email": "admin@example.com",
                        "is_verified": True
                    }
                }
                
                # Add configured admin user if different from default
                if self.admin_username and self.admin_username != "admin":
                    self.credentials[self.admin_username] = {
                        "name": "Administrator",
                        "password": self.hash_password(self.admin_password or "password"),
                        "email": f"{self.admin_username}@example.com",
                        "is_verified": True
                    }
                
                self._save_credentials()
    
    def create_default_credentials(self):
        """Create default credentials file with admin user."""
        # Use environment variable or a secure random password as default
        admin_password = self.admin_password or ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
            
        default_credentials = {
            "admin": {
                "name": "Administrator",
                "password": self.hash_password(admin_password),
                "email": "admin@example.com",
                "is_verified": True
            }
        }
        
        # Add configured admin user if different from default
        if self.admin_username and self.admin_username != "admin":
            default_credentials[self.admin_username] = {
                "name": "Administrator",
                "password": self.hash_password(self.admin_password),
                "email": f"{self.admin_username}@example.com",
                "is_verified": True
            }
        
        with open(self.credentials_path, "wb") as f:
            pickle.dump(default_credentials, f)
    
    def load_credentials(self):
        """Load credentials from file."""
        with open(self.credentials_path, "rb") as f:
            return pickle.load(f)
    
    def hash_password(self, password):
        """Hash a password for storing."""
        try:
            if bcrypt:
                # Use bcrypt for secure password hashing
                return bcrypt.hashpw(password.encode(), bcrypt.gensalt())
            else:
                # Fallback to SHA-256 if bcrypt is not available
                return hashlib.sha256(password.encode()).hexdigest()
        except Exception as e:
            print(f"Error in hash_password: {e}")
            # Fallback to SHA-256 if there's an error with bcrypt
            return hashlib.sha256(password.encode()).hexdigest()
    
    def generate_verification_token(self):
        """Generate a random verification token."""
        import secrets
        return secrets.token_urlsafe(32)
    
    def add_user(self, username, password, name, email, require_verification=True):
        """Add a new user to the credentials."""
        # Check if username already exists
        if self.is_deployment:
            conn = sqlite3.connect(get_db_path())
            cursor = conn.cursor()
            
            try:
                # Check if username already exists
                cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
                if cursor.fetchone():
                    conn.close()
                    return False, "Username already exists"
                
                # Check if email already exists
                cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
                if cursor.fetchone():
                    conn.close()
                    return False, "Email address already registered. Please use a different email."
                
                # Generate verification token if required
                verification_token = None
                verification_expiry = None
                if require_verification:
                    verification_token = self.generate_verification_token()
                    verification_expiry = (datetime.now() + timedelta(hours=24)).isoformat()
                
                # Generate a unique ID and current timestamp
                user_id = str(uuid.uuid4())
                created_at = datetime.now().isoformat()
                
                # Debug information
                print(f"Adding new user: {username}")
                print(f"User ID: {user_id}")
                print(f"Created at: {created_at}")
                
                # Add the new user
                cursor.execute('''
                INSERT INTO users (id, username, password, name, email, created_at, is_verified, verification_token, verification_expiry)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user_id,
                    username, 
                    self.hash_password(password), 
                    name, 
                    email,
                    created_at,
                    0 if require_verification else 1,  # 0 = not verified, 1 = verified
                    verification_token, 
                    verification_expiry
                ))
                
                conn.commit()
                
                # Send verification email if required
                if require_verification:
                    email_sent = self.send_verification_email(email, username, verification_token)
                    if not email_sent:
                        # If email fails, still create the account but warn the user
                        conn.close()
                        return True, "Account created but verification email could not be sent. Please contact support."
                
                conn.close()
                
                if require_verification:
                    return True, "Account created successfully. Please check your email to verify your account."
                else:
                    return True, "Account created successfully."
            
            except Exception as e:
                print(f"Error adding user: {str(e)}")
                import traceback
                traceback.print_exc()
                conn.close()
                return False, f"Error adding user: {str(e)}"
        else:
            # For development mode
            if username in self.credentials:
                return False, "Username already exists"
            
            # Check if email already exists
            for existing_username, user_data in self.credentials.items():
                if user_data.get("email") == email:
                    return False, "Email address already registered. Please use a different email."
            
            # Add the new user
            self.credentials[username] = {
                "name": name,
                "password": self.hash_password(password),
                "email": email,
                "is_verified": not require_verification
            }
            
            # If verification is required, generate a token and send email
            if require_verification:
                verification_token = self.generate_verification_token()
                self.credentials[username]["verification_token"] = verification_token
                self.credentials[username]["verification_expiry"] = datetime.now() + timedelta(hours=24)
                
                # Send verification email
                email_sent = self.send_verification_email(email, username, verification_token)
                if not email_sent:
                    # If email fails, still create the account but warn the user
                    self._save_credentials()
                    return True, "Account created but verification email could not be sent. Please contact support."
            
            # Save the updated credentials
            self._save_credentials()
            
            if require_verification:
                return True, "Account created successfully. Please check your email to verify your account."
            else:
                return True, "Account created successfully."
    
    def _save_credentials(self):
        """Save credentials to file."""
        with open(self.credentials_path, "wb") as f:
            pickle.dump(self.credentials, f)
    
    def verify_user(self, token):
        """Verify a user's email using the verification token."""
        if self.is_deployment:
            conn = sqlite3.connect(get_db_path())
            cursor = conn.cursor()
            
            try:
                # Find the user with this token
                cursor.execute(
                    "SELECT id, username, verification_expiry FROM users WHERE verification_token = ?", 
                    (token,)
                )
                result = cursor.fetchone()
                
                if not result:
                    conn.close()
                    return False, "Invalid verification token."
                
                user_id, username, expiry_str = result
                
                # Check if token is expired
                if expiry_str:
                    expiry = datetime.fromisoformat(expiry_str)
                    if expiry < datetime.now():
                        conn.close()
                        return False, "Verification token has expired. Please request a new one."
                
                # Update the user to verified status
                cursor.execute(
                    "UPDATE users SET is_verified = 1, verification_token = NULL, verification_expiry = NULL WHERE id = ?",
                    (user_id,)
                )
                conn.commit()
                conn.close()
                return True, f"Email verified successfully! You can now log in as {username}."
            except Exception as e:
                conn.close()
                return False, f"Error verifying email: {str(e)}"
        else:
            # For development mode
            for username, user_data in self.credentials.items():
                if user_data.get("verification_token") == token:
                    # Check if token is expired
                    expiry = user_data.get("verification_expiry")
                    if expiry and expiry < datetime.now():
                        return False, "Verification token has expired. Please request a new one."
                    
                    # Mark user as verified
                    self.credentials[username]["is_verified"] = True
                    self.credentials[username].pop("verification_token", None)
                    self.credentials[username].pop("verification_expiry", None)
                    self._save_credentials()
                    return True, f"Email verified successfully! You can now log in as {username}."
            
            return False, "Invalid verification token."
    
    def verify_user_without_token(self, username):
        """Mark a user as verified without requiring a token (for admin or fallback)."""
        if self.is_deployment:
            conn = sqlite3.connect(get_db_path())
            cursor = conn.cursor()
            
            cursor.execute('''
            UPDATE users SET is_verified = 1, verification_token = NULL, verification_expiry = NULL
            WHERE username = ?
            ''', (username,))
            
            conn.commit()
            conn.close()
        else:
            if username in self.credentials:
                self.credentials[username]["is_verified"] = True
                self.credentials[username]["verification_token"] = None
                self.credentials[username]["verification_expiry"] = None
                
                with open(self.credentials_path, "wb") as f:
                    pickle.dump(self.credentials, f)
    
    def resend_verification_email(self, email):
        """Resend the verification email to the user."""
        try:
            if self.is_deployment:
                conn = sqlite3.connect(get_db_path())
                cursor = conn.cursor()
                
                # Get user by email
                cursor.execute("SELECT username, verification_token FROM users WHERE email = ? AND is_verified = 0", (email,))
                result = cursor.fetchone()
                
                if not result:
                    # For testing purposes, allow resending to any email
                    # Instead of returning an error, generate a new token
                    username = email.split('@')[0]  # Use part of email as username
                    verification_token = secrets.token_urlsafe(32)
                    
                    # Check if this email exists but is already verified
                    cursor.execute("SELECT username FROM users WHERE email = ? AND is_verified = 1", (email,))
                    verified_user = cursor.fetchone()
                    
                    if verified_user:
                        # Update the existing user with a new verification token
                        cursor.execute(
                            "UPDATE users SET verification_token = ?, is_verified = 0 WHERE email = ?",
                            (verification_token, email)
                        )
                        conn.commit()
                        username = verified_user[0]
                    else:
                        # This is completely new - just for testing, we'll pretend it exists
                        st.warning("For testing: Creating a temporary user record for this email")
                    
                    conn.close()
                    
                    # Send the verification email
                    success = self.send_verification_email(email, username, verification_token)
                    if not success:
                        return False, "Failed to send verification email. Please try again later."
                    
                    return True, "Verification email sent. Please check your inbox."
                
                username, verification_token = result
                
                # Generate a new token if needed
                if not verification_token:
                    verification_token = secrets.token_urlsafe(32)
                    cursor.execute(
                        "UPDATE users SET verification_token = ? WHERE email = ?",
                        (verification_token, email)
                    )
                    conn.commit()
                
                conn.close()
                
                # Send the verification email
                success = self.send_verification_email(email, username, verification_token)
                if not success:
                    return False, "Failed to send verification email. Please try again later."
                
                return True, "Verification email sent. Please check your inbox."
            else:
                # Find user by email
                username = None
                for existing_username, user_data in self.credentials.items():
                    if user_data.get("email") == email and not user_data.get("is_verified", False):
                        username = existing_username
                        break
                
                if not username:
                    # For testing purposes, allow resending to any email
                    # Instead of returning an error, generate a new token
                    username = email.split('@')[0]  # Use part of email as username
                    verification_token = secrets.token_urlsafe(32)
                    
                    # Check if this email exists but is already verified
                    verified_user = None
                    for user, details in self.credentials.items():
                        if details.get("email") == email and details.get("is_verified", False):
                            verified_user = user
                            break
                    
                    if verified_user:
                        # Update the existing user with a new verification token
                        self.credentials[verified_user]["verification_token"] = verification_token
                        self.credentials[verified_user]["is_verified"] = False
                        self.credentials[verified_user]["verification_expiry"] = datetime.now() + timedelta(hours=24)
                        self._save_credentials()
                        username = verified_user
                    else:
                        # This is completely new - just for testing, we'll pretend it exists
                        st.warning("For testing: Creating a temporary user record for this email")
                    
                    # Send the verification email
                    success = self.send_verification_email(email, username, verification_token)
                    if not success:
                        return False, "Failed to send verification email. Please try again later."
                    
                    return True, "Verification email sent. Please check your inbox."
                
                # Generate a new token
                verification_token = secrets.token_urlsafe(32)
                self.credentials[username]["verification_token"] = verification_token
                self.credentials[username]["verification_expiry"] = datetime.now() + timedelta(hours=24)
                
                # Save the updated credentials
                self._save_credentials()
                
                # Send the verification email
                success = self.send_verification_email(email, username, verification_token)
                if not success:
                    return False, "Failed to send verification email. Please try again later."
                
                return True, "Verification email sent. Please check your inbox."
        except Exception as e:
            print(f"Error in resend_verification_email: {e}")
            return False, f"An error occurred: {str(e)}"
    
    def verify_password(self, username, password):
        """Verify if the password is correct for the given username."""
        if self.is_deployment:
            # Use the _verify_password_db method which has better error handling
            return self._verify_password_db(username, password)
        else:
            if username not in self.credentials:
                return False
            
            # Check if the user is verified
            if not self.credentials[username].get("is_verified", True):
                return False
            
            # Verify the password
            stored_password = self.credentials[username]["password"]
            
            try:
                if bcrypt and self._is_bcrypt_hash(stored_password):
                    # Handle bcrypt password
                    if isinstance(stored_password, str):
                        stored_password = stored_password.encode()
                    return bcrypt.checkpw(password.encode(), stored_password)
                else:
                    # Handle non-bcrypt password or when bcrypt is not available
                    return stored_password == self.hash_password(password)
            except Exception as e:
                print(f"Error in verify_password: {e}")
                # Fall back to direct comparison if there's an error
                return stored_password == self.hash_password(password)
    
    def _verify_password_db(self, username, password):
        """Verify password against database."""
        conn = None
        try:
            # Ensure database is initialized
            self._init_db_if_needed()
            
            # Debug information
            print(f"Verifying password for user: {username}")
            print(f"Database path: {get_db_path()}")
            
            # Get database connection
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            # Get the stored password hash and verification status
            cursor.execute("SELECT password, is_verified FROM users WHERE username = ?", (username,))
            result = cursor.fetchone()
            
            if not result:
                print(f"User not found in database: {username}")
                return False
                
            stored_password, is_verified = result
            
            # Check if user is verified
            if not is_verified:
                print(f"User {username} is not verified")
                return False
            
            # Verify the password
            password_verified = False
            try:
                if bcrypt and self._is_bcrypt_hash(stored_password):
                    # If stored password is already a bcrypt hash
                    print(f"Using bcrypt verification for user: {username}")
                    if isinstance(stored_password, str):
                        stored_password = stored_password.encode()
                    password_verified = bcrypt.checkpw(password.encode(), stored_password)
                else:
                    # If stored password is a sha256 hash (from before bcrypt was added)
                    print(f"Using sha256 verification for user: {username}")
                    password_verified = stored_password == hashlib.sha256(password.encode()).hexdigest()
            except Exception as e:
                print(f"Error verifying password with bcrypt in _verify_password_db: {e}")
                # Fallback to sha256
                print(f"Falling back to sha256 verification for user: {username}")
                password_verified = stored_password == hashlib.sha256(password.encode()).hexdigest()
            
            # Update last login time if password matches
            if password_verified:
                print(f"Password verified for user: {username}")
                now = datetime.now().isoformat()
                cursor.execute("UPDATE users SET last_login = ? WHERE username = ?", (now, username))
                conn.commit()
            else:
                print(f"Password verification failed for user: {username}")
                
            return password_verified
            
        except Exception as e:
            print(f"Error in _verify_password_db: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            if conn:
                conn.close()
    
    def get_user_info(self, username):
        """Get information about a user."""
        if self.is_deployment:
            try:
                # Ensure database is initialized
                self._init_db_if_needed()
                
                # Debug information
                print(f"Getting user info for: {username}")
                print(f"Database path: {get_db_path()}")
                
                # Get database connection
                conn = sqlite3.connect(get_db_path())
                cursor = conn.cursor()
                
                cursor.execute("SELECT name, email, is_verified FROM users WHERE username = ?", (username,))
                result = cursor.fetchone()
                conn.close()
                
                if result is None:
                    print(f"User not found in database: {username}")
                    return None
                
                name, email, is_verified = result
                user_info = {
                    "name": name,
                    "email": email,
                    "is_verified": bool(is_verified)
                }
                print(f"User info retrieved for {username}: {user_info}")
                return user_info
            except Exception as e:
                print(f"Error in get_user_info: {e}")
                import traceback
                traceback.print_exc()
                return None
        else:
            if username not in self.credentials:
                return None
            
            user_data = self.credentials[username]
            return {
                "name": user_data.get("name", "User"),
                "email": user_data.get("email", ""),
                "is_verified": user_data.get("is_verified", True)
            }
    
    def _get_user_info_db(self, username):
        """Get user information from database."""
        try:
            # Ensure database is initialized
            self._init_db_if_needed()
            
            # Debug information
            print(f"Getting user info from DB for: {username}")
            print(f"Database path: {get_db_path()}")
            
            # Get database connection
            conn = sqlite3.connect(get_db_path())
            cursor = conn.cursor()
            
            cursor.execute("SELECT name, email FROM users WHERE username = ?", (username,))
            result = cursor.fetchone()
            
            conn.close()
            
            if result is None:
                print(f"User not found in database: {username}")
                return None
            
            user_info = {
                "name": result[0],
                "email": result[1]
            }
            print(f"User info retrieved from DB for {username}: {user_info}")
            return user_info
        except Exception as e:
            print(f"Error in _get_user_info_db: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def login(self):
        """Display login form and handle authentication."""
        # Initialize session state for authentication
        if "authenticated" not in st.session_state:
            st.session_state.authenticated = False
            st.session_state.username = None
            st.session_state.name = None
            st.session_state.show_signup = False
        
        # If already authenticated, return early
        if st.session_state.authenticated:
            return st.session_state.name, True, st.session_state.username
        
        # Display login form
        st.title("Technical Blog Generator")
        st.subheader("Login")
        
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")
            
            if submit:
                if self.verify_password(username, password):
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.session_state.name = self.get_user_info(username)["name"]
                    st.success(f"Welcome to TechMuse, {self.get_user_info(username)['name']}!")
                    st.rerun()
                else:
                    st.error("Invalid username or password")
        
        # Add a signup option
        if st.button("Need an account? Sign up"):
            st.session_state.show_signup = True
            st.rerun()
        
        # Show signup form if requested
        if st.session_state.show_signup:
            self.show_signup_form()
        
        # Return authentication status
        return None, False, None
    
    def show_signup_form(self):
        """Display signup form."""
        st.subheader("Create an Account")
        
        with st.form("signup_form"):
            new_username = st.text_input("Choose a Username", placeholder="Choose a username")
            new_password = st.text_input("Choose a Password", type="password", placeholder="Choose a secure password")
            
            # Password strength indicator
            if new_password:
                password_strength = self._check_password_strength(new_password)
                if password_strength == "weak":
                    st.markdown('<div class="password-strength weak">Weak password</div>', unsafe_allow_html=True)
                elif password_strength == "medium":
                    st.markdown('<div class="password-strength medium">Medium strength</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="password-strength strong">Strong password</div>', unsafe_allow_html=True)
            
            confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")
            full_name = st.text_input("Full Name", placeholder="Your full name")
            email = st.text_input("Email Address", placeholder="Your email address")
            
            # Submit button
            signup_button = st.form_submit_button("Create Account", use_container_width=True)
        
        # Handle form submission
        if signup_button:
            # Simple validation
            if not new_username or not new_password or not full_name or not email:
                st.error("All fields are required")
            elif len(new_username) < 4:
                st.error("Username must be at least 4 characters long")
            elif new_password != confirm_password:
                st.error("Passwords do not match")
            elif self._check_password_strength(new_password) == "weak":
                st.error("Please use a stronger password")
            elif "@" not in email or "." not in email:
                st.error("Please enter a valid email address")
            else:
                # Add the new user
                success, message = self.add_user(new_username, new_password, full_name, email)
                if success:
                    st.success(message)
                    st.info("You can now log in with your new credentials")
                    st.session_state.show_signup = False
                    st.rerun()
                else:
                    st.error(message)
        
        # Add a link to switch to login
        if st.button("Already have an account? Sign in", key="to_login", use_container_width=True):
            st.session_state.show_signup = False
            st.rerun()
    
    def _check_password_strength(self, password):
        """Check password strength."""
        # Basic password strength check
        if len(password) < 8:
            return "weak"
        
        # Check for complexity
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(not c.isalnum() for c in password)
        
        if has_upper and has_lower and has_digit and has_special:
            return "strong"
        elif (has_upper or has_lower) and (has_digit or has_special):
            return "medium"
        else:
            return "weak"
    
    def logout(self):
        """Log out the current user."""
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.username = None
            st.session_state.name = None
            st.rerun()

    def show_admin_page(self):
        """Display admin page for user management."""
        if not self.is_admin(st.session_state.username):
            st.error("You don't have permission to access this page.")
            return
        
        st.title("User Management")
        
        # Get all users
        users = self.get_all_users()
        
        if not users:
            st.info("No users found in the database.")
            return
        
        # Display users in a table
        user_data = []
        for user in users:
            user_data.append({
                "ID": user[0],
                "Username": user[1],
                "Name": user[3],
                "Email": user[4],
                "Created": user[5],
                "Last Login": user[6] if user[6] else "Never"
            })
        
        st.dataframe(user_data)
        
        # Add user management options
        st.subheader("User Actions")
        
        # Delete user
        with st.expander("Delete User"):
            username_to_delete = st.selectbox(
                "Select user to delete",
                options=[user[1] for user in users if user[1] != st.session_state.username],
                key="delete_user_select"
            )
            
            if st.button("Delete User", key="delete_user_button"):
                if username_to_delete:
                    success, message = self.delete_user(username_to_delete)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
        
        # Reset password
        with st.expander("Reset User Password"):
            username_to_reset = st.selectbox(
                "Select user to reset password",
                options=[user[1] for user in users if user[1] != st.session_state.username],
                key="reset_password_select"
            )
            
            new_password = st.text_input("New Password", type="password", key="new_password")
            confirm_password = st.text_input("Confirm New Password", type="password", key="confirm_new_password")
            
            if st.button("Reset Password", key="reset_password_button"):
                if not username_to_reset:
                    st.error("Please select a user")
                elif not new_password:
                    st.error("Please enter a new password")
                elif new_password != confirm_password:
                    st.error("Passwords do not match")
                else:
                    success, message = self.reset_password(username_to_reset, new_password)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
    
    def is_admin(self, username):
        """Check if the user is an admin."""
        if not username:
            return False
            
        if self.is_deployment:
            # In deployment mode, check the database
            conn = sqlite3.connect(get_db_path())
            cursor = conn.cursor()
            
            # Get the first user (admin)
            cursor.execute("SELECT id FROM users ORDER BY id ASC LIMIT 1")
            first_user = cursor.fetchone()
            
            # Get the current user
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            current_user = cursor.fetchone()
            
            conn.close()
            
            if not first_user or not current_user:
                return False
            
            # The first user is admin
            return current_user[0] == first_user[0]
        
        # In local development, admin user is admin
        return username == "admin" or (self.admin_username and username == self.admin_username)
    
    def get_all_users(self):
        """Get all users from the database."""
        if not self.is_deployment:
            # Convert credentials dictionary to list format
            users = []
            for username, data in self.credentials.items():
                users.append((
                    "N/A",  # No ID in file-based storage
                    username,
                    data["password"],
                    data["name"],
                    data["email"],
                    "N/A",  # No creation date in file-based storage
                    "N/A"   # No last login in file-based storage
                ))
            return users
        
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users ORDER BY created_at ASC")
        users = cursor.fetchall()
        
        conn.close()
        return users
    
    def delete_user(self, username):
        """Delete a user."""
        if not self.is_deployment:
            if username not in self.credentials:
                return False, "User not found"
            
            del self.credentials[username]
            
            with open(self.credentials_path, "wb") as f:
                pickle.dump(self.credentials, f)
            
            return True, f"User {username} deleted successfully"
        
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM users WHERE username = ?", (username,))
            conn.commit()
            conn.close()
            return True, f"User {username} deleted successfully"
        except Exception as e:
            conn.close()
            return False, f"Error deleting user: {str(e)}"
    
    def reset_password(self, username, new_password):
        """Reset a user's password."""
        hashed_password = self.hash_password(new_password)
        
        if not self.is_deployment:
            if username not in self.credentials:
                return False, "User not found"
            
            self.credentials[username]["password"] = hashed_password
            
            with open(self.credentials_path, "wb") as f:
                pickle.dump(self.credentials, f)
            
            return True, f"Password for {username} reset successfully"
        
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        
        try:
            cursor.execute("UPDATE users SET password = ? WHERE username = ?", (hashed_password, username))
            conn.commit()
            conn.close()
            return True, f"Password for {username} reset successfully"
        except Exception as e:
            conn.close()
            return False, f"Error resetting password: {str(e)}"
    
    def check_user_exists(self, username):
        """Check if a user exists."""
        if self.is_deployment:
            try:
                # Ensure database is initialized
                self._init_db_if_needed()
                
                # Get database connection
                conn = sqlite3.connect(get_db_path())
                cursor = conn.cursor()
                
                # Debug information
                print(f"Checking if user exists: {username}")
                print(f"Database path: {get_db_path()}")
                
                cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
                result = cursor.fetchone()
                conn.close()
                
                exists = result is not None
                print(f"User {username} exists: {exists}")
                return exists
            except Exception as e:
                print(f"Error in check_user_exists: {e}")
                import traceback
                traceback.print_exc()
                # Return False on error to be safe
                return False
        else:
            return username in self.credentials
    
    def check_user_verified(self, username):
        """Check if a user is verified."""
        if self.is_deployment:
            try:
                # Ensure database is initialized
                self._init_db_if_needed()
                
                # Get database connection
                conn = sqlite3.connect(get_db_path())
                cursor = conn.cursor()
                
                # Debug information
                print(f"Checking verification status for user: {username}")
                print(f"Database path: {get_db_path()}")
                
                # Check if user exists first
                cursor.execute("SELECT username FROM users WHERE username = ?", (username,))
                user_exists = cursor.fetchone() is not None
                
                if not user_exists:
                    print(f"User {username} not found in database")
                    conn.close()
                    return False
                
                # Now check verification status
                cursor.execute("SELECT is_verified FROM users WHERE username = ?", (username,))
                result = cursor.fetchone()
                conn.close()
                
                verified = result is not None and result[0] == 1
                print(f"User {username} verification status: {verified}")
                return verified
            except Exception as e:
                print(f"Error in check_user_verified: {e}")
                import traceback
                traceback.print_exc()
                # Return False on error to be safe
                return False
        else:
            if username not in self.credentials:
                return False
            return self.credentials[username].get("is_verified", True)
    
    def get_user_email(self, username):
        """Get a user's email address."""
        if self.is_deployment:
            try:
                # Ensure database is initialized
                self._init_db_if_needed()
                
                # Get database connection
                conn = sqlite3.connect(get_db_path())
                cursor = conn.cursor()
                
                # Debug information
                print(f"Getting email for user: {username}")
                print(f"Database path: {get_db_path()}")
                
                cursor.execute("SELECT email FROM users WHERE username = ?", (username,))
                result = cursor.fetchone()
                conn.close()
                
                email = result[0] if result else None
                print(f"Email for user {username}: {email}")
                return email
            except Exception as e:
                print(f"Error in get_user_email: {e}")
                import traceback
                traceback.print_exc()
                return None
        else:
            if username not in self.credentials:
                return None
            return self.credentials[username].get("email")

    def send_verification_email(self, email, username, token):
        """Send a verification email to the user using Resend."""
        try:
            # Debug: Print environment variables
            print("Environment variables:")
            print(f"VERIFIED_EMAIL_FROM: {os.getenv('VERIFIED_EMAIL_FROM', 'Not set')}")
            print(f"RESEND_API_KEY: {'Set' if os.getenv('RESEND_API_KEY') else 'Not set'}")
            
            # Get configuration from Streamlit secrets or environment variables
            api_key = os.getenv("RESEND_API_KEY", "")
            if not api_key and hasattr(st, "secrets") and "RESEND_API_KEY" in st.secrets:
                api_key = st.secrets["RESEND_API_KEY"]
            
            # Create verification URL
            # Determine if we're running on Streamlit Cloud
            is_cloud = (
                "STREAMLIT_SHARING" in os.environ or 
                "STREAMLIT_CLOUD" in os.environ or
                os.getenv("DEPLOYMENT", "").lower() == "true" or
                (hasattr(st, "secrets") and st.secrets.get("DEPLOYMENT", "").lower() == "true")
            )
            
            # Set the base URL based on environment
            if is_cloud:
                # For Streamlit Cloud, use the deployment URL
                base_url = os.getenv("BASE_URL", "https://techmuse.streamlit.app")
                if hasattr(st, "secrets") and "BASE_URL" in st.secrets:
                    base_url = st.secrets["BASE_URL"]
            else:
                # For local development
                base_url = "http://localhost:8501"
                if hasattr(st, "secrets") and "BASE_URL" in st.secrets:
                    base_url = st.secrets["BASE_URL"]
            
            # Create verification URL
            verification_url = f"{base_url}?verify={token}"
            
            # Always show the verification link in local development
            if not is_cloud:
                st.info(f"📧 **Verification Link**: [Click here to verify your email]({verification_url})")
            
            # Set Resend API key
            if not api_key:
                st.warning("⚠️ Resend API key not configured. Email verification will not work.")
                return False
                
            resend.api_key = api_key
            
            # Email content
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto;">
                <div style="background-color: #f8f9fa; padding: 20px; text-align: center; border-bottom: 3px solid #4361EE;">
                    <h1 style="color: #4361EE;">Welcome to TechMuse!</h1>
                </div>
                <div style="padding: 20px;">
                    <p>Hello {username},</p>
                    <p>Thank you for signing up. Please verify your email address by clicking the button below:</p>
                    <p style="text-align: center;">
                        <a href="{verification_url}" style="display: inline-block; background-color: #4361EE; color: white; text-decoration: none; padding: 10px 20px; border-radius: 5px; font-weight: bold;">Verify Email Address</a>
                    </p>
                    <p>Or copy and paste this URL into your browser:</p>
                    <p style="background-color: #f8f9fa; padding: 10px; border-radius: 5px; word-break: break-all;">{verification_url}</p>
                    <p>This link will expire in 24 hours.</p>
                    <p>If you did not sign up for TechMuse, please ignore this email.</p>
                </div>
                <div style="background-color: #f8f9fa; padding: 20px; text-align: center; font-size: 12px; color: #666;">
                    <p>&copy; 2025 TechMuse. All rights reserved.</p>
                </div>
            </body>
            </html>
            """
            
            # Get the verified domain email or use Resend's onboarding email
            from_email = os.getenv("VERIFIED_EMAIL_FROM")
            
            # Debug info
            print(f"From email from env: {from_email}")
            
            # Check Streamlit secrets if available
            if not from_email and hasattr(st, "secrets") and "VERIFIED_EMAIL_FROM" in st.secrets:
                from_email = st.secrets["VERIFIED_EMAIL_FROM"]
                print(f"From email from secrets: {from_email}")
            
            # If still not set, use Resend's onboarding email
            if not from_email:
                from_email = "onboarding@resend.dev"
                print(f"Using default onboarding email: {from_email}")
            
            from_name = os.getenv("RESEND_FROM_NAME", "TechMuse")
            if hasattr(st, "secrets") and "RESEND_FROM_NAME" in st.secrets:
                from_name = st.secrets["RESEND_FROM_NAME"]
            
            # Send email to the user's actual email address
            params = {
                "from": f"{from_name} <{from_email}>",
                "to": email,  # Send to the user's actual email
                "subject": "Verify Your TechMuse Account",
                "html": html_content,
            }
            
            print(f"Sending verification email to: {email}")
            print(f"From email: {from_email}")
            response = resend.Emails.send(params)
            print(f"Response: {response}")
            
            if response and "id" in response:
                print(f"Email sent successfully with ID: {response['id']}")
                st.success(f"✉️ Verification email sent to {email}. Please check your inbox.")
                return True
            else:
                print(f"Failed to send email: {response}")
                st.error("Failed to send verification email. Please try again later.")
                # Still show the verification link in case email fails
                st.info(f"📧 **Verification Link**: [Click here to verify your email]({verification_url})")
                return False
                
        except Exception as e:
            print(f"Error in send_verification_email: {str(e)}")
            print(f"Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            st.error(f"Error sending verification email: {str(e)}")
            # Still show the verification link in case of error
            st.info(f"📧 **Verification Link**: [Click here to verify your email]({verification_url})")
            return False

    def _is_bcrypt_hash(self, password_hash):
        """Check if a password hash is in bcrypt format."""
        if isinstance(password_hash, bytes):
            try:
                # Try to decode it to check if it starts with the bcrypt prefix
                decoded = password_hash.decode('utf-8')
                return decoded.startswith('$2a$') or decoded.startswith('$2b$')
            except UnicodeDecodeError:
                # If it can't be decoded as UTF-8, it's probably not a bcrypt hash
                return False
        elif isinstance(password_hash, str):
            return password_hash.startswith('$2a$') or password_hash.startswith('$2b$')
        return False

    def _init_db_if_needed(self):
        """Initialize the database connection for deployment mode."""
        try:
            # Get the database path
            db_path = get_db_path()
            print(f"Database path: {db_path}")
            
            # Ensure the directory exists
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            
            # Initialize the database connection
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Create users table if it doesn't exist
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                created_at TEXT NOT NULL,
                last_login TEXT,
                is_verified INTEGER DEFAULT 0,
                verification_token TEXT,
                verification_expiry TEXT
            )
            ''')
            
            conn.commit()
            
            # Check if admin user exists, create if not
            cursor.execute("SELECT * FROM users WHERE username = ?", (self.admin_username or "admin",))
            if cursor.fetchone() is None and (self.admin_username or self.admin_password):
                # Create admin user
                admin_id = str(uuid.uuid4())
                now = datetime.now().isoformat()
                hashed_password = self.hash_password(self.admin_password or "password")
                
                cursor.execute('''
                INSERT INTO users (id, username, password, name, email, created_at, is_verified)
                VALUES (?, ?, ?, ?, ?, ?, 1)
                ''', (
                    admin_id, 
                    self.admin_username or "admin", 
                    hashed_password, 
                    "Administrator", 
                    f"{self.admin_username or 'admin'}@example.com", 
                    now
                ))
                
                conn.commit()
                print(f"Created admin user: {self.admin_username or 'admin'}")
            
            conn.close()
            return True
        except Exception as e:
            print(f"Error in _init_db_if_needed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _get_db_connection(self):
        """Get a database connection."""
        return sqlite3.connect(get_db_path())

# Create a singleton instance
authenticator = SimpleAuthenticator()

def login():
    """Wrapper function to call the authenticator's login method."""
    return authenticator.login()

def logout():
    """Wrapper function to call the authenticator's logout method."""
    authenticator.logout()

def require_auth():
    """
    Require authentication to access the app.
    Returns the user's name and username if authenticated.
    """
    # Check if the user is already authenticated
    if "authenticated" in st.session_state and st.session_state.authenticated:
        return st.session_state.name, st.session_state.username
    
    # Check for verification token in URL parameters
    if "verify" in st.query_params:
        token = st.query_params["verify"]
        success, message = authenticator.verify_user(token)
        if success:
            st.success(message)
            # Remove the token from the URL
            st.query_params.clear()
        else:
            st.error(message)
    
    # Initialize session state for resend verification
    if "show_resend" not in st.session_state:
        st.session_state.show_resend = False
    
    # Create a clean login interface
    st.markdown("""
    <style>
    /* Center the entire app content */
    .main .block-container {
        max-width: 100%;
        padding-top: 3rem;
        padding-bottom: 3rem;
    }
    
    /* Hide Streamlit elements we don't need */
    .stApp header {
        display: none;
    }
    
    /* Welcome title styling */
    .welcome-title {
        font-size: 1.75rem;
        font-weight: 600;
        color: #4361EE;
        margin-bottom: 1.5rem;
        text-align: center;
    }
    
    /* App logo styling */
    .app-logo {
        text-align: center;
        margin-bottom: 1rem;
    }
    
    .app-logo img {
        width: 80px;
        height: 80px;
    }
    
    /* Custom styling for the input fields */
    .stTextInput > div > div > input {
        max-width: 300px;
        padding: 0.5rem 0.75rem;
        font-size: 0.9rem;
        border: 1px solid #E5E7EB;
        border-radius: 6px;
        background-color: #F9FAFB;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #4361EE;
        box-shadow: 0 0 0 3px rgba(67, 97, 238, 0.15);
    }
    
    /* Custom styling for the button */
    .stButton > button {
        max-width: 300px;
        background-color: #4361EE;
        color: white;
        font-weight: 500;
        padding: 0.5rem 1rem;
        border-radius: 6px;
        border: none;
        cursor: pointer;
        transition: background-color 0.2s;
    }
    
    .stButton > button:hover {
        background-color: #3651D4;
    }
    
    /* Auth tabs styling */
    .auth-tabs {
        display: flex;
        justify-content: center;
        margin-bottom: 1.5rem;
        border-bottom: 1px solid #E5E7EB;
    }
    
    .auth-tab {
        padding: 0.75rem 1.5rem;
        cursor: pointer;
        font-weight: 500;
        color: #6B7280;
        border-bottom: 2px solid transparent;
        transition: all 0.2s;
    }
    
    .auth-tab:hover {
        color: #4361EE;
    }
    
    .auth-tab.active {
        color: #4361EE;
        border-bottom-color: #4361EE;
    }
    
    /* Auth card styling */
    .auth-card {
        background-color: transparent;
        border-radius: 12px;
        padding: 0;
        max-width: 400px;
        width: 100%;
        margin: 0 auto;
    }
    
    /* Remove empty space */
    .element-container {
        margin-bottom: 0 !important;
    }
    
    /* Fix button spacing */
    .stButton {
        margin-top: 1rem;
        margin-bottom: 0.5rem;
    }
    
    /* Fix form spacing */
    .stForm > div:first-child {
        padding-bottom: 0 !important;
    }
    
    /* Hide empty containers */
    .element-container:empty {
        display: none !important;
    }
    
    /* Remove all white backgrounds */
    div.stTextInput, div.stButton, div.stMarkdown {
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }
    
    /* Remove any white boxes */
    div[data-testid="stVerticalBlock"] {
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0 !important;
        margin: 0 !important;
    }
    
    /* Remove any white containers */
    div.css-1r6slb0, div.css-1y4p8pa, div.css-1vq4p4l, div.css-1d3bhpq {
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }
    
    /* Streamlit container fix */
    .stContainer, .st-emotion-cache-1y4p8pa {
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0 !important;
    }
    
    /* Password strength indicator */
    .password-strength {
        margin-top: 0.5rem;
        font-size: 0.8rem;
    }
    
    .password-strength.weak {
        color: #EF4444;
    }
    
    .password-strength.medium {
        color: #F59E0B;
    }
    
    .password-strength.strong {
        color: #10B981;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Initialize session state for auth UI
    if "auth_tab" not in st.session_state:
        st.session_state.auth_tab = "login"
    
    # Create columns for a centered form with more space on the sides
    col1, col2, col3 = st.columns([2, 1, 2])
    
    with col2:
        # App logo
        st.markdown("""
        <div class="app-logo">
            <div style="font-size: 3rem; color: #4361EE;">📝</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Welcome title without the container box
        st.markdown('<div class="welcome-title">Welcome to TechMuse</div>', unsafe_allow_html=True)
        
        # Show resend verification form if needed
        if st.session_state.show_resend:
            with st.form("resend_verification_form"):
                st.subheader("Resend Verification Email")
                email = st.text_input("Email Address", placeholder="Enter your email address")
                submit = st.form_submit_button("Resend Verification Email", use_container_width=True)
                
                if submit:
                    if email:
                        success, message = authenticator.resend_verification_email(email)
                        if success:
                            st.success(message)
                            st.session_state.show_resend = False
                        else:
                            st.error(message)
                    else:
                        st.error("Please enter your email address")
            
            if st.button("Back to Login", use_container_width=True):
                st.session_state.show_resend = False
                st.rerun()
            
            # Stop execution to show only the resend form
            st.stop()
        
        # Create tabs for login and signup
        st.markdown(f"""
        <div class="auth-tabs">
            <div class="auth-tab {'active' if st.session_state.auth_tab == 'login' else ''}" 
                 onclick="window.location.href='?tab=login'">Sign In</div>
            <div class="auth-tab {'active' if st.session_state.auth_tab == 'signup' else ''}" 
                 onclick="window.location.href='?tab=signup'">Sign Up</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Check URL parameters for tab selection
        if "tab" in st.query_params and st.query_params["tab"] in ["login", "signup"]:
            st.session_state.auth_tab = st.query_params["tab"]
        
        # Auth card
        st.markdown('<div class="auth-card">', unsafe_allow_html=True)
        
        # Login form
        if st.session_state.auth_tab == "login":
            with st.container():
                username = st.text_input("Username", key="login_username", placeholder="Enter your username")
                password = st.text_input("Password", type="password", key="login_password", placeholder="Enter your password")
                login_button = st.button("Sign In", key="login_button", use_container_width=True)
                
                # Add a link to switch to signup
                st.markdown("<div style='height: 10px'></div>", unsafe_allow_html=True)
                if st.button("Need an account? Sign up", key="to_signup", use_container_width=True):
                    st.session_state.auth_tab = "signup"
                    st.query_params.update(tab="signup")
                    st.rerun()
                
                # Add a link to resend verification email
                if st.button("Didn't receive verification email?", key="to_resend", use_container_width=True):
                    st.session_state.show_resend = True
                    st.rerun()
            
                # Check credentials when the login button is clicked
                if login_button:
                    if not username or not password:
                        st.error("Please enter both username and password")
                    else:
                        # Use the authenticator to verify credentials
                        if authenticator.verify_password(username, password):
                            # Set session state to authenticated
                            st.session_state.authenticated = True
                            st.session_state.username = username
                            st.session_state.name = authenticator.get_user_info(username)["name"]
                            
                            # Rerun the app to reflect the authenticated state
                            st.rerun()
                        else:
                            # Check if user exists but is not verified
                            user_exists = authenticator.check_user_exists(username)
                            is_verified = authenticator.check_user_verified(username)
                            
                            if user_exists and not is_verified:
                                st.error("Your account has not been verified. Please check your email for a verification link or request a new one.")
                                # Show option to resend verification email
                                if st.button("Resend verification email", key="resend_from_login", use_container_width=True):
                                    email = authenticator.get_user_email(username)
                                    if email:
                                        success, message = authenticator.resend_verification_email(email)
                                        if success:
                                            st.success(message)
                                        else:
                                            st.error(message)
                            else:
                                st.error("Invalid username or password")
        
        # Signup form
        else:
            with st.container():
                # Create a form to ensure all fields are submitted together
                with st.form("signup_form"):
                    new_username = st.text_input("Choose a Username", placeholder="Choose a username")
                    new_password = st.text_input("Choose a Password", type="password", placeholder="Choose a secure password")
                    
                    # Password strength indicator
                    if new_password:
                        password_strength = authenticator._check_password_strength(new_password)
                        if password_strength == "weak":
                            st.markdown('<div class="password-strength weak">Weak password</div>', unsafe_allow_html=True)
                        elif password_strength == "medium":
                            st.markdown('<div class="password-strength medium">Medium strength</div>', unsafe_allow_html=True)
                        else:
                            st.markdown('<div class="password-strength strong">Strong password</div>', unsafe_allow_html=True)
                    
                    confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")
                    full_name = st.text_input("Full Name", placeholder="Your full name")
                    email = st.text_input("Email Address", placeholder="Your email address")
                    
                    # Submit button
                    signup_button = st.form_submit_button("Create Account", use_container_width=True)
                
                # Handle form submission
                if signup_button:
                    # Simple validation
                    if not new_username or not new_password or not full_name or not email:
                        st.error("All fields are required")
                    elif len(new_username) < 4:
                        st.error("Username must be at least 4 characters long")
                    elif new_password != confirm_password:
                        st.error("Passwords do not match")
                    elif authenticator._check_password_strength(new_password) == "weak":
                        st.error("Please use a stronger password")
                    elif "@" not in email or "." not in email:
                        st.error("Please enter a valid email address")
                    else:
                        # Add the new user
                        success, message = authenticator.add_user(new_username, new_password, full_name, email)
                        if success:
                            st.success(message)
                            st.info("You can now log in with your new credentials")
                            st.session_state.show_signup = False
                            st.rerun()
                        else:
                            st.error(message)
                
                # Add a link to switch to login
                if st.button("Already have an account? Sign in", key="to_login", use_container_width=True):
                    st.session_state.auth_tab = "login"
                    st.query_params.update(tab="login")
                    st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Add a simple footer
        st.markdown("""
        <div class="login-footer">
            Secure Login • TechMuse 2025
        </div>
        """, unsafe_allow_html=True)
    
    # Stop execution if not authenticated
    st.stop()
