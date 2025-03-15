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
    """Require authentication before proceeding."""
    st.markdown("""
    <style>
        /* Modern login container */
        .login-container {
            max-width: 400px;
            margin: 2rem auto;
            padding: 2rem;
            background: white;
            border-radius: 16px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
            animation: float-in 0.5s ease-out;
        }
        
        /* Float in animation */
        @keyframes float-in {
            0% {
                opacity: 0;
                transform: translateY(20px);
            }
            100% {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        /* Login header */
        .login-header {
            text-align: center;
            margin-bottom: 2rem;
        }
        
        .login-header h1 {
            color: #4361EE;
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }
        
        .login-header p {
            color: #6B7280;
            font-size: 1rem;
        }
        
        /* Input fields */
        .stTextInput input {
            width: 100%;
            padding: 0.75rem 1rem;
            border: 2px solid #E5E7EB;
            border-radius: 8px;
            font-size: 1rem;
            transition: all 0.3s ease;
        }
        
        .stTextInput input:focus {
            border-color: #4361EE;
            box-shadow: 0 0 0 3px rgba(67, 97, 238, 0.15);
        }
        
        /* Login button */
        .stButton button {
            width: 100%;
            background-color: #4361EE;
            color: white;
            padding: 0.75rem 1rem;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            font-size: 1rem;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .stButton button:hover {
            background-color: #3A56D4;
            transform: translateY(-2px);
        }
        
        /* Error message */
        .stAlert {
            border-radius: 8px;
            margin-bottom: 1rem;
            animation: shake 0.5s ease-in-out;
        }
        
        @keyframes shake {
            0%, 100% { transform: translateX(0); }
            25% { transform: translateX(-5px); }
            75% { transform: translateX(5px); }
        }
        
        /* Dark mode support */
        @media (prefers-color-scheme: dark) {
            .login-container {
                background: #1E1E1E;
            }
            .login-header h1 {
                color: #90CAF9;
            }
            .login-header p {
                color: #E0E0E0;
            }
            .stTextInput input {
                background-color: #2D2D2D;
                color: #E0E0E0;
                border-color: #555;
            }
            .stTextInput input:focus {
                border-color: #90CAF9;
            }
        }
    </style>
    """, unsafe_allow_html=True)

    # Initialize session state
    if 'name' not in st.session_state:
        st.session_state.name = None
    if 'authentication_status' not in st.session_state:
        st.session_state.authentication_status = None
    if 'username' not in st.session_state:
        st.session_state.username = None

    # If not authenticated, show login form
    if not st.session_state.authentication_status:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        st.markdown("""
            <div class="login-header">
                <h1>👋 Welcome Back</h1>
                <p>Please sign in to continue</p>
            </div>
        """, unsafe_allow_html=True)

        username = st.text_input('Username', placeholder='Enter your username')
        password = st.text_input('Password', type='password', placeholder='Enter your password')
        
        # Center the login button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            login = st.button('Sign In')

        if login:
            if username == "admin" and password == "admin":  # Replace with your actual authentication logic
                st.session_state.authentication_status = True
                st.session_state.name = "Administrator"
                st.session_state.username = username
                st.rerun()
            else:
                st.error('⚠️ Invalid username or password')

        st.markdown('</div>', unsafe_allow_html=True)
        st.stop()

    return st.session_state.name, st.session_state.username

def logout():
    """Logout button with improved styling."""
    if st.button('🚪 Sign Out', key='logout'):
        st.session_state.authentication_status = None
        st.session_state.name = None
        st.session_state.username = None
        st.rerun() 