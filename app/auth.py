import streamlit as st
import os
from pathlib import Path
import pickle
import hashlib
import sqlite3
import uuid
from datetime import datetime
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
        email TEXT UNIQUE NOT NULL,
        created_at TEXT NOT NULL,
        last_login TEXT
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
        INSERT INTO users (id, username, password, name, email, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (admin_id, ADMIN_USERNAME, hashed_password, "Administrator", "admin@example.com", now))
        
        conn.commit()
    
    conn.close()

# Initialize the database
init_db()

# Simple authentication with SQLite support
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
                "email": "admin@example.com"
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
    
    def add_user(self, username, password, name, email):
        """Add a new user to the credentials."""
        # In deployment, add user to database
        if self.is_deployment:
            return self._add_user_to_db(username, password, name, email)
        
        # In local development with production flag, we'll now allow adding users
        # Remove the production mode restriction
        # if self.is_production:
        #     return False, "Cannot add users in production mode"
        
        # In local development, add to file
        # Check if username already exists
        if username in self.credentials:
            return False, "Username already exists"
        
        # Add the new user
        self.credentials[username] = {
            "name": name,
            "password": self.hash_password(password),
            "email": email
        }
        
        # Save the updated credentials
        with open(self.credentials_path, "wb") as f:
            pickle.dump(self.credentials, f)
        
        return True, "User added successfully"
    
    def _add_user_to_db(self, username, password, name, email):
        """Add a new user to the database."""
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        
        # Check if username already exists
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        if cursor.fetchone() is not None:
            conn.close()
            return False, "Username already exists"
        
        # Check if email already exists
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        if cursor.fetchone() is not None:
            conn.close()
            return False, "Email already exists"
        
        # Add the new user
        user_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        hashed_password = self.hash_password(password)
        
        try:
            cursor.execute('''
            INSERT INTO users (id, username, password, name, email, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, username, hashed_password, name, email, now))
            
            conn.commit()
            conn.close()
            return True, "User added successfully"
        except Exception as e:
            conn.close()
            return False, f"Error adding user: {str(e)}"
    
    def verify_password(self, username, password):
        """Verify if the password is correct for the given username."""
        # In deployment, verify against database
        if self.is_deployment:
            return self._verify_password_db(username, password)
        
        # In production local mode, check against environment variables/secrets
        if self.is_production and username == ADMIN_USERNAME:
            return self.hash_password(password) == self.hash_password(ADMIN_PASSWORD)
        
        # Otherwise check against the credentials file
        if username not in self.credentials:
            return False
        
        hashed_password = self.hash_password(password)
        return hashed_password == self.credentials[username]["password"]
    
    def _verify_password_db(self, username, password):
        """Verify password against database."""
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        
        cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        
        if result is None:
            conn.close()
            return False
        
        stored_password = result[0]
        hashed_password = self.hash_password(password)
        
        # Update last login time if password matches
        if hashed_password == stored_password:
            now = datetime.now().isoformat()
            cursor.execute("UPDATE users SET last_login = ? WHERE username = ?", (now, username))
            conn.commit()
        
        conn.close()
        return hashed_password == stored_password
    
    def get_user_info(self, username):
        """Get user information."""
        # In deployment, get from database
        if self.is_deployment:
            return self._get_user_info_db(username)
        
        # In production local mode with admin user
        if self.is_production and username == ADMIN_USERNAME:
            return {
                "name": "Administrator",
                "email": "admin@example.com"
            }
        
        # Otherwise get from credentials file
        if username not in self.credentials:
            return None
        
        return {
            "name": self.credentials[username]["name"],
            "email": self.credentials[username]["email"]
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
            
                # Check credentials when the login button is clicked
                if login_button:
                    # Use the authenticator to verify credentials
                    if authenticator.verify_password(username, password):
                        # Set session state to authenticated
                        st.session_state.authenticated = True
                        st.session_state.username = username
                        st.session_state.name = authenticator.get_user_info(username)["name"]
                        
                        # Rerun the app to reflect the authenticated state
                        st.rerun()
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

def main():
    # Check if the user is authenticated
    if "authenticated" in st.session_state and st.session_state.authenticated:
        # Display the main app content
        st.title("Technical Blog Generator")
        st.write("Welcome to the Technical Blog Generator!")
        
        # Add an admin page link for admins
        if authenticator.is_admin(st.session_state.username):
            if st.button("Admin Page"):
                authenticator.show_admin_page()
    else:
        # Display the login form
        authenticator.login()

if __name__ == "__main__":
    main()
