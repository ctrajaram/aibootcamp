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
        border-radius: 6px;
        padding: 0.6rem 1rem;
        border: none;
    }
    
    .stButton > button:hover {
        background-color: #3A56D4;
        border: none;
    }
    
    /* Footer styling */
    .login-footer {
        margin-top: 1rem;
        text-align: center;
        font-size: 0.8rem;
        color: #6B7280;
    }
    
    /* Center all elements */
    div[data-testid="column"] {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }
    
    /* Make labels centered */
    .stTextInput label {
        text-align: center;
        display: block;
        margin-bottom: 0.5rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Create columns for a centered form with more space on the sides
    col1, col2, col3 = st.columns([2, 1, 2])
    
    with col2:
        # Welcome title without the container box
        st.markdown('<div class="welcome-title">Welcome</div>', unsafe_allow_html=True)
        
        # Create a simple login form
        username = st.text_input("Username", key="username_input", placeholder="Enter your username")
        password = st.text_input("Password", type="password", key="password_input", placeholder="Enter your password")
        login_button = st.button("Sign In", key="login_button")
        
        # Add a simple footer
        st.markdown("""
        <div class="login-footer">
            Technical Blog Generator • Secure Login
        </div>
        """, unsafe_allow_html=True)
        
        # Check credentials when the login button is clicked
        if login_button:
            # Use the authenticator to verify credentials
            if authenticator.verify_password(username, password):
                # Set session state to authenticated
                st.session_state.authenticated = True
                st.session_state.username = username
                st.session_state.name = authenticator.credentials[username]["name"]
                
                # Rerun the app to reflect the authenticated state
                st.rerun()
            else:
                st.error("Invalid username or password")
    
    # Stop execution if not authenticated
    st.stop()

def logout():
    """Logout button with improved styling."""
    if st.button('🚪 Sign Out', key='logout'):
        st.session_state.authentication_status = None
        st.session_state.name = None
        st.session_state.username = None
        st.rerun() 