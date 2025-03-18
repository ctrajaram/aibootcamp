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
import bcrypt
import secrets
import string
import requests
import resend
from dotenv import load_dotenv

# Set Resend API key directly
os.environ["RESEND_API_KEY"] = "re_GqtZRXhH_7EFuSJpn3AfU2rvf3KDg5tUp"
os.environ["RESEND_FROM_EMAIL"] = "onboarding@resend.dev"
os.environ["RESEND_FROM_NAME"] = "TechMuse"
os.environ["BASE_URL"] = "http://localhost:8501"
os.environ["EDUCATIONAL_MODE"] = "false"

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
    # In production, use a path that will be persisted in the deployment
    if os.getenv("STREAMLIT_DEPLOYMENT", "0") == "1":
        # Use the .streamlit folder which is persistent in Streamlit Cloud
        os.makedirs(os.path.join(os.path.expanduser("~"), ".streamlit"), exist_ok=True)
        return os.path.join(os.path.expanduser("~"), ".streamlit", "techmuse.db")
    else:
        # In development, use a local file
        return "techmuse.db"

def init_db():
    """Initialize the database with required tables."""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    # Create users table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        created_at TEXT NOT NULL,
        last_login TEXT,
        is_verified INTEGER DEFAULT 0,
        verification_token TEXT,
        verification_expiry TEXT
    )
    ''')
    
    conn.commit()
    
    # Check if admin user exists, create if not
    cursor.execute("SELECT * FROM users WHERE username = ?", (ADMIN_USERNAME,))
    if cursor.fetchone() is None and ADMIN_USERNAME != "default_username":
        # Create admin user
        admin_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        hashed_password = hashlib.sha256(ADMIN_PASSWORD.encode()).hexdigest()
        
        cursor.execute('''
        INSERT INTO users (id, username, password, name, email, created_at, is_verified)
        VALUES (?, ?, ?, ?, ?, ?, 1)
        ''', (admin_id, ADMIN_USERNAME, hashed_password, "Administrator", "admin@example.com", now))
        
        conn.commit()
    
    conn.close()

# Initialize the database
init_db()

# Email sending functions
def send_verification_email(email, username, token):
    """Send a verification email to the user using Resend."""
    try:
        # Create verification URL
        base_url = "http://localhost:8501"  # Hardcoded for testing
        verification_url = f"{base_url}?verify={token}"
        
        # Always show the verification link as a fallback
        st.info(f"📧 **Verification Link**: [Click here to verify your email]({verification_url})")
        
        # Use the same pattern as the successful test script
        api_key = "re_GqtZRXhH_7EFuSJpn3AfU2rvf3KDg5tUp"
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
        
        # In testing mode, Resend only allows sending to the verified email
        verified_email = "ctrwillow@gmail.com"
        
        # Check if the user's email matches the verified email
        if email.lower() == verified_email.lower():
            # Send email using Resend - exact same pattern as test_resend.py
            params = {
                "from": "onboarding@resend.dev",
                "to": email,
                "subject": "Verify Your TechMuse Account",
                "html": html_content,
            }
            
            print(f"Sending verification email to verified address: {email}")
            response = resend.Emails.send(params)
            print(f"Response: {response}")
            
            if response and "id" in response:
                print(f"Email sent successfully with ID: {response['id']}")
                st.success(f"✉️ Verification email sent to {email}. Please check your inbox.")
                return True
            else:
                print(f"Failed to send email: {response}")
                return False
        else:
            # For non-verified emails in testing mode, just show a message
            print(f"Cannot send to {email} in testing mode. Only {verified_email} is allowed.")
            st.warning(f"⚠️ In testing mode: Emails can only be sent to {verified_email}.")
            st.info("Please use the verification link above to verify your account.")
            return True  # Return true so the account creation continues
                
    except Exception as e:
        print(f"Error in send_verification_email: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

class SimpleAuthenticator:
    def __init__(self):
        """Initialize the authenticator with credentials from database or file."""
        self.credentials_path = Path("auth_credentials.pkl")
        
        # Check if we're in production (environment variables or secrets set)
        self.is_production = (ADMIN_USERNAME != "default_username" and 
                             ADMIN_PASSWORD != "default_password")
        
        # Check if we're in a Streamlit deployment
        self.is_deployment = os.getenv("STREAMLIT_DEPLOYMENT", "0") == "1"
        
        if not self.is_deployment:
            # In local development, use the file for backward compatibility
            if not self.credentials_path.exists():
                self.create_default_credentials()
            
            # Load credentials from file
            self.credentials = self.load_credentials()
        else:
            # In deployment, we'll use the database directly
            # We don't need to load credentials into memory
            self.credentials = {}
    
    def create_default_credentials(self):
        """Create default credentials file with admin user."""
        default_credentials = {
            "admin": {
                "name": "Administrator",
                "password": self.hash_password("admin"),
                "email": "admin@example.com",
                "is_verified": True
            }
        }
        
        with open(self.credentials_path, "wb") as f:
            pickle.dump(default_credentials, f)
    
    def load_credentials(self):
        """Load credentials from file."""
        with open(self.credentials_path, "rb") as f:
            return pickle.load(f)
    
    def hash_password(self, password):
        """Hash a password for storing."""
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
                
                # Generate verification token if required
                verification_token = None
                verification_expiry = None
                if require_verification:
                    verification_token = self.generate_verification_token()
                    verification_expiry = (datetime.now() + timedelta(hours=24)).isoformat()
                
                # Add the new user
                cursor.execute('''
                INSERT INTO users (username, password, name, email, is_verified, verification_token, verification_expiry)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    username, 
                    self.hash_password(password), 
                    name, 
                    email, 
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
                conn.close()
                return False, f"Error adding user: {str(e)}"
        else:
            # For development mode
            if username in self.credentials:
                return False, "Username already exists"
            
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
                for user, details in self.credentials.items():
                    if details.get("email") == email and not details.get("is_verified", False):
                        username = user
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
            conn = sqlite3.connect(get_db_path())
            cursor = conn.cursor()
            cursor.execute("SELECT password, is_verified FROM users WHERE username = ?", (username,))
            result = cursor.fetchone()
            conn.close()
            
            if result is None:
                return False
            
            stored_password, is_verified = result
            
            # Check if the user is verified
            if not is_verified:
                return False
            
            # Verify the password
            return stored_password == self.hash_password(password)
        else:
            if username not in self.credentials:
                return False
            
            # Check if the user is verified
            if not self.credentials[username].get("is_verified", True):
                return False
            
            # Verify the password
            return self.credentials[username]["password"] == self.hash_password(password)
    
    def _verify_password_db(self, username, password):
        """Verify password against database."""
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        
        cursor.execute("SELECT password, is_verified FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        
        if result is None:
            conn.close()
            return False
        
        stored_password, is_verified = result
        
        # Check if user is verified
        if not is_verified:
            conn.close()
            return False
        
        hashed_password = self.hash_password(password)
        
        # Update last login time if password matches
        if hashed_password == stored_password:
            now = datetime.now().isoformat()
            cursor.execute("UPDATE users SET last_login = ? WHERE username = ?", (now, username))
            conn.commit()
        
        conn.close()
        return hashed_password == stored_password
    
    def get_user_info(self, username):
        """Get information about a user."""
        if self.is_deployment:
            conn = sqlite3.connect(get_db_path())
            cursor = conn.cursor()
            cursor.execute("SELECT name, email, is_verified FROM users WHERE username = ?", (username,))
            result = cursor.fetchone()
            conn.close()
            
            if result is None:
                return None
            
            name, email, is_verified = result
            return {
                "name": name,
                "email": email,
                "is_verified": bool(is_verified)
            }
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
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        
        cursor.execute("SELECT name, email FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        
        conn.close()
        
        if result is None:
            return None
        
        return {
            "name": result[0],
            "email": result[1]
        }
    
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
        # In deployment, check against database
        if self.is_deployment:
            # For simplicity, we'll consider the first user as admin
            # In a real app, you'd have a role field in the database
            conn = sqlite3.connect(get_db_path())
            cursor = conn.cursor()
            
            cursor.execute("SELECT id FROM users ORDER BY created_at ASC LIMIT 1")
            first_user = cursor.fetchone()
            
            if not first_user:
                conn.close()
                return False
            
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            current_user = cursor.fetchone()
            
            conn.close()
            
            if not current_user:
                return False
            
            # The first user is admin
            return current_user[0] == first_user[0]
        
        # In local development, admin user is admin
        return username == "admin" or (self.is_production and username == ADMIN_USERNAME)
    
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
            conn = sqlite3.connect(get_db_path())
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            result = cursor.fetchone()
            conn.close()
            return result is not None
        else:
            return username in self.credentials
    
    def check_user_verified(self, username):
        """Check if a user is verified."""
        if self.is_deployment:
            conn = sqlite3.connect(get_db_path())
            cursor = conn.cursor()
            cursor.execute("SELECT is_verified FROM users WHERE username = ?", (username,))
            result = cursor.fetchone()
            conn.close()
            return result is not None and result[0] == 1
        else:
            if username not in self.credentials:
                return False
            return self.credentials[username].get("is_verified", True)
    
    def get_user_email(self, username):
        """Get a user's email address."""
        if self.is_deployment:
            conn = sqlite3.connect(get_db_path())
            cursor = conn.cursor()
            cursor.execute("SELECT email FROM users WHERE username = ?", (username,))
            result = cursor.fetchone()
            conn.close()
            return result[0] if result else None
        else:
            if username not in self.credentials:
                return None
            return self.credentials[username].get("email")

    def send_verification_email(self, email, username, token):
        """Send a verification email to the user using Resend."""
        try:
            # Create verification URL
            base_url = "http://localhost:8501"  # Hardcoded for testing
            verification_url = f"{base_url}?verify={token}"
            
            # Always show the verification link as a fallback
            st.info(f"📧 **Verification Link**: [Click here to verify your email]({verification_url})")
            
            # Use the same pattern as the successful test script
            api_key = "re_GqtZRXhH_7EFuSJpn3AfU2rvf3KDg5tUp"
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
            
            # In testing mode, Resend only allows sending to the verified email
            verified_email = "ctrwillow@gmail.com"
            
            # Check if the user's email matches the verified email
            if email.lower() == verified_email.lower():
                # Send email using Resend - exact same pattern as test_resend.py
                params = {
                    "from": "onboarding@resend.dev",
                    "to": email,
                    "subject": "Verify Your TechMuse Account",
                    "html": html_content,
                }
                
                print(f"Sending verification email to verified address: {email}")
                response = resend.Emails.send(params)
                print(f"Response: {response}")
                
                if response and "id" in response:
                    print(f"Email sent successfully with ID: {response['id']}")
                    st.success(f"✉️ Verification email sent to {email}. Please check your inbox.")
                    return True
                else:
                    print(f"Failed to send email: {response}")
                    return False
            else:
                # For non-verified emails in testing mode, just show a message
                print(f"Cannot send to {email} in testing mode. Only {verified_email} is allowed.")
                st.warning(f"⚠️ In testing mode: Emails can only be sent to {verified_email}.")
                st.info("Please use the verification link above to verify your account.")
                return True  # Return true so the account creation continues
                    
        except Exception as e:
            print(f"Error in send_verification_email: {str(e)}")
            print(f"Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            return False

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
                        # Add the new user with verification required
                        success, message = authenticator.add_user(new_username, new_password, full_name, email, require_verification=True)
                        if success:
                            st.success(message)
                            st.info("Please check your email to verify your account.")
                            # Switch to login tab
                            st.session_state.auth_tab = "login"
                            st.query_params.update(tab="login")
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
