import streamlit as st
import os
from pathlib import Path
import pickle
import hashlib

# Simple authentication without external dependencies
class SimpleAuthenticator:
    def __init__(self):
        """Initialize the authenticator with default credentials."""
        self.credentials_path = Path("auth_credentials.pkl")
        
        # Create default credentials if they don't exist
        if not self.credentials_path.exists():
            self.create_default_credentials()
        
        # Load credentials
        self.credentials = self.load_credentials()
    
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
        """Create a simple hash of the password."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, username, password):
        """Verify if the password is correct for the given username."""
        if username not in self.credentials:
            return False
        
        hashed_password = self.hash_password(password)
        return hashed_password == self.credentials[username]["password"]
    
    def login(self):
        """Display login form and handle authentication."""
        # Initialize session state for authentication
        if "authenticated" not in st.session_state:
            st.session_state.authenticated = False
            st.session_state.username = None
            st.session_state.name = None
        
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
                    st.session_state.name = self.credentials[username]["name"]
                    st.success(f"Welcome, {self.credentials[username]['name']}!")
                    st.rerun()
                else:
                    st.error("Invalid username or password")
        
        # Return authentication status
        return None, False, None
    
    def logout(self):
        """Log out the current user."""
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.username = None
            st.session_state.name = None
            st.rerun()

# Create a singleton instance
authenticator = SimpleAuthenticator()

def login():
    """Wrapper function to call the authenticator's login method."""
    return authenticator.login()

def logout():
    """Wrapper function to call the authenticator's logout method."""
    authenticator.logout()

def require_auth():
    """Require authentication to access the page."""
    name, auth_status, username = login()
    
    if not auth_status:
        st.stop()
    
    return name, username 