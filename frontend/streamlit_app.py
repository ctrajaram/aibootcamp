import streamlit as st

# Configure the app - MUST be the first Streamlit command
st.set_page_config(
    page_title="Technical Blog Generator",
    page_icon="📝",
    layout="wide"
)

# Add authentication
import sys
import os
# Add the app directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.auth import require_auth, logout
# Import ResearchTopic from researcher module
from app.agents.researcher import ResearchTopic, research_topic

# Initialize session state for theme settings
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False
if 'compact_view' not in st.session_state:
    st.session_state.compact_view = True  # Set compact view as default

# Require authentication
name, username = require_auth()

import requests
from typing import List, Dict
import json
import datetime
from dotenv import load_dotenv
from pydantic import ValidationError
import markdown
import base64
import uuid
from pathlib import Path
import time
import re

# Load environment variables
load_dotenv()

# Define paths for saved blogs
SAVED_BLOGS_DIR = Path("saved_blogs")
SAVED_BLOGS_INDEX = SAVED_BLOGS_DIR / "index.json"

# Ensure the directory exists
if not SAVED_BLOGS_DIR.exists():
    SAVED_BLOGS_DIR.mkdir(parents=True)
    
# Initialize or load the blogs index
def load_blogs_index() -> Dict:
    if not SAVED_BLOGS_INDEX.exists():
        with open(SAVED_BLOGS_INDEX, 'w') as f:
            json.dump({"blogs": []}, f)
        return {"blogs": []}
    
    try:
        with open(SAVED_BLOGS_INDEX, 'r') as f:
            return json.load(f)
    except:
        return {"blogs": []}

# Save a blog to the local database
def save_blog(title: str, content: str, metadata: Dict) -> str:
    # Generate a unique ID
    blog_id = str(uuid.uuid4())
    
    # Create a blog entry
    blog_entry = {
        "id": blog_id,
        "title": title,
        "created_at": datetime.datetime.now().isoformat(),
        "metadata": metadata,
        "preview": content[:200] + "..." if len(content) > 200 else content
    }
    
    # Save the content to a file
    blog_file = SAVED_BLOGS_DIR / f"{blog_id}.md"
    with open(blog_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Update the index
    index = load_blogs_index()
    index["blogs"].append(blog_entry)
    
    with open(SAVED_BLOGS_INDEX, 'w') as f:
        json.dump(index, f, indent=2)
    
    return blog_id

# Custom CSS for styling
st.markdown("""
<style>
    /* Import fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Color palette - Bootstrap inspired with custom accent */
    :root {
        --primary: #0d6efd;       /* Bootstrap primary blue */
        --primary-dark: #0b5ed7;  /* Darker shade for hover states */
        --secondary: #6c757d;     /* Bootstrap secondary gray */
        --success: #198754;       /* Bootstrap success green */
        --info: #0dcaf0;          /* Bootstrap info cyan */
        --warning: #ffc107;       /* Bootstrap warning yellow */
        --danger: #dc3545;        /* Bootstrap danger red */
        --light: #f8f9fa;         /* Bootstrap light gray */
        --dark: #212529;          /* Bootstrap dark gray */
        --accent: #7952b3;        /* Custom purple accent */
        --accent-light: #9461e3;  /* Lighter accent for hover */
        --border-color: #dee2e6;  /* Bootstrap border color */
        --text-primary: #212529;  /* Main text color */
        --text-secondary: #6c757d; /* Secondary text color */
        --text-muted: #adb5bd;    /* Muted text color */
        --bg-light: #f8f9fa;      /* Light background */
        --bg-white: #ffffff;      /* White background */
        --shadow-sm: 0 .125rem .25rem rgba(0,0,0,.075); /* Small shadow */
        --shadow: 0 .5rem 1rem rgba(0,0,0,.15);         /* Medium shadow */
        --shadow-lg: 0 1rem 3rem rgba(0,0,0,.175);      /* Large shadow */
        --radius: 0.375rem;       /* Border radius */
        --radius-sm: 0.25rem;     /* Small border radius */
        --radius-lg: 0.5rem;      /* Large border radius */
        --spacing-1: 0.25rem;     /* 4px */
        --spacing-2: 0.5rem;      /* 8px */
        --spacing-3: 1rem;        /* 16px */
        --spacing-4: 1.5rem;      /* 24px */
        --spacing-5: 3rem;        /* 48px */
    }
    
    /* Base styles */
    * {
        font-family: 'Inter', sans-serif;
        box-sizing: border-box;
    }
    
    /* Improved spacing for the entire app */
    .block-container {
        padding-top: var(--spacing-4) !important;
        padding-bottom: var(--spacing-4) !important;
        max-width: 1200px !important;
        margin: 0 auto !important;
    }
    
    /* Section spacing */
    .element-container {
        margin-bottom: var(--spacing-3) !important;
        padding: var(--spacing-2) 0 !important;
    }
    
    /* Modern main header with consistent color */
    .main-header {
        font-size: 2.8rem;
        color: var(--primary);
        font-weight: 700;
        margin-bottom: var(--spacing-4);
        text-align: center;
        padding: var(--spacing-3);
        text-shadow: 0px 2px 4px rgba(0,0,0,0.1);
        letter-spacing: -0.5px;
        background-image: url("data:image/svg+xml,%3Csvg width='100' height='100' viewBox='0 0 100 100' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M11 18c3.866 0 7-3.134 7-7s-3.134-7-7-7-7 3.134-7 7 3.134 7 7 7zm48 25c3.866 0 7-3.134 7-7s-3.134-7-7-7-7 3.134-7 7 3.134 7 7 7zm-43-7c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zm63 31c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zM34 90c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zm56-76c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zM12 86c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm28-65c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm23-11c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zm-6 60c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm29 22c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zM32 63c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zm57-13c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zm-9-21c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2zM60 91c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2zM35 41c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2zM12 60c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2z' fill='%23e0e0e0' fill-opacity='0.1' fill-rule='evenodd'/%3E%3C/svg%3E");
        background-position: center;
        border-radius: var(--radius-lg);
    }
    
    /* Modern sub-header */
    .sub-header {
        font-size: 1.5rem;
        color: var(--accent);
        font-weight: 600;
        margin-top: var(--spacing-4);
        border-bottom: 2px solid var(--border-color);
        padding-bottom: var(--spacing-2);
        letter-spacing: -0.3px;
    }
    
    /* Modern description */
    .description {
        color: var(--text-secondary);
        font-size: 1.1rem;
        margin: 0 auto var(--spacing-3) auto;
        background-color: transparent;
        padding: var(--spacing-3);
        border-radius: var(--radius);
        box-shadow: none;
        max-width: 90%;
        text-align: center;
        line-height: 1.6;
        font-weight: 400;
    }
    
    /* Modern success box */
    .success-box {
        background-color: #d1e7dd;
        padding: var(--spacing-3);
        border-radius: var(--radius);
        margin: var(--spacing-3) 0;
        box-shadow: var(--shadow-sm);
        border-left: 5px solid var(--success);
    }
    
    /* Modern info box */
    .info-box {
        background-color: #cff4fc;
        padding: var(--spacing-3);
        border-radius: var(--radius);
        margin: var(--spacing-3) 0;
        box-shadow: var(--shadow-sm);
        border-left: 5px solid var(--info);
    }
    
    /* Bootstrap-style buttons with consistent sizing and icons */
    .stButton button {
        background-color: var(--primary);
        color: white;
        font-weight: 500;
        border-radius: 8px;
        padding: var(--spacing-2) var(--spacing-3);
        border: none;
        text-transform: none;
        letter-spacing: normal;
        box-shadow: var(--shadow-sm);
        transition: all 0.2s ease;
        width: 200px !important;
        height: 44px !important;
        font-size: 1rem !important;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: var(--spacing-2) auto !important;
        position: relative;
        overflow: hidden;
    }
    
    .stButton button:hover {
        background-color: var(--primary-dark);
        box-shadow: var(--shadow);
        transform: translateY(-2px);
    }
    
    .stButton button:active {
        transform: translateY(0);
        box-shadow: var(--shadow-sm);
    }
    
    .stButton button:after {
        content: "";
        position: absolute;
        top: 50%;
        left: 50%;
        width: 5px;
        height: 5px;
        background: rgba(255, 255, 255, 0.5);
        opacity: 0;
        border-radius: 100%;
        transform: scale(1, 1) translate(-50%);
        transform-origin: 50% 50%;
    }
    
    .stButton button:focus:not(:active)::after {
        animation: ripple 1s ease-out;
    }
    
    @keyframes ripple {
        0% {
            transform: scale(0, 0);
            opacity: 0.5;
        }
        20% {
            transform: scale(25, 25);
            opacity: 0.3;
        }
        100% {
            opacity: 0;
            transform: scale(40, 40);
        }
    }
    
    /* Sign out button specific styling */
    button[kind="secondary"], 
    [data-testid="baseButton-secondary"] {
        background-color: var(--secondary) !important;
        color: white !important;
        font-weight: 500 !important;
        border-radius: 8px !important;
        width: 200px !important;
        height: 44px !important;
    }
    
    button[kind="secondary"]:hover, 
    [data-testid="baseButton-secondary"]:hover {
        background-color: #5c636a !important;
        transform: translateY(-2px) !important;
        box-shadow: var(--shadow) !important;
    }
    
    button[kind="secondary"]:active, 
    [data-testid="baseButton-secondary"]:active {
        transform: translateY(0) !important;
        box-shadow: var(--shadow-sm) !important;
    }
    
    /* Generate content button - make it stand out with accent color */
    button[data-testid="baseButton-primary"],
    button[key="generate_content_button"] {
        background-color: var(--accent) !important;
        width: 220px !important;
        height: 48px !important;
        box-shadow: var(--shadow) !important;
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        position: relative;
        overflow: hidden;
        border-radius: 8px !important;
    }
    
    button[data-testid="baseButton-primary"]:hover,
    button[key="generate_content_button"]:hover {
        background-color: var(--accent-light) !important;
        transform: translateY(-3px) !important;
        box-shadow: 0 8px 15px rgba(0,0,0,0.2) !important;
    }
    
    button[data-testid="baseButton-primary"]:active,
    button[key="generate_content_button"]:active {
        transform: translateY(-1px) !important;
    }
    
    /* Modern download button */
    .stDownloadButton button {
        background-color: var(--success);
        color: white;
        font-weight: 500;
        border-radius: 8px;
        box-shadow: var(--shadow-sm);
        width: 200px !important;
        height: 44px !important;
        margin: var(--spacing-2) auto !important;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    .stDownloadButton button:hover {
        background-color: #157347;
        box-shadow: var(--shadow);
        transform: translateY(-2px);
    }
    
    .stDownloadButton button:active {
        transform: translateY(0);
        box-shadow: var(--shadow-sm);
    }
    
    /* Add icons to buttons using pseudo-elements */
    button[key="generate_content_button"]:before {
        content: "🚀";
        margin-right: 8px;
    }
    
    .stDownloadButton button[title*="Markdown"]:before {
        content: "📥";
        margin-right: 8px;
    }
    
    .stDownloadButton button[title*="HTML"]:before {
        content: "📄";
        margin-right: 8px;
    }
    
    button[key="sidebar_logout_button"]:before {
        content: "🚪";
        margin-right: 8px;
    }
    
    /* Visual indicators for complexity level */
    .complexity-indicator {
        display: inline-flex;
        align-items: center;
        margin-top: 5px;
        background-color: var(--bg-light);
        padding: 4px 8px;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: 500;
    }
    
    .complexity-beginner {
        color: #0ca678;
        border: 1px solid #0ca678;
    }
    
    .complexity-beginner:before {
        content: "🟢";
        margin-right: 5px;
    }
    
    .complexity-intermediate {
        color: #f59f00;
        border: 1px solid #f59f00;
    }
    
    .complexity-intermediate:before {
        content: "🟠";
        margin-right: 5px;
    }
    
    .complexity-advanced {
        color: #e03131;
        border: 1px solid #e03131;
    }
    
    .complexity-advanced:before {
        content: "🔴";
        margin-right: 5px;
    }
    
    /* Modern section headers with icons */
    [data-testid="stMarkdownContainer"] h3 {
        color: var(--primary);
        font-weight: 700;
        font-size: 1.35rem;
        margin: var(--spacing-4) 0 var(--spacing-2) 0;
        display: flex;
        align-items: center;
        letter-spacing: -0.3px;
    }
    
    /* Add icons to specific section headers */
    [data-testid="stMarkdownContainer"] h3:before {
        font-family: "Material Icons";
        margin-right: 8px;
        background-color: var(--bg-light);
        width: 32px;
        height: 32px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        border-radius: 50%;
        color: var(--primary);
        font-size: 18px;
    }
    
    /* Modern tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: var(--bg-light);
        padding: var(--spacing-2);
        border-radius: var(--radius);
        margin: var(--spacing-3) 0;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: var(--radius);
        padding: var(--spacing-2) var(--spacing-3);
        font-weight: 500;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: var(--primary) !important;
        color: white !important;
    }
    
    /* Modern chat interface */
    [data-testid="stChatMessage"] {
        background-color: var(--bg-light);
        border-radius: var(--radius);
        padding: var(--spacing-3);
        margin-bottom: var(--spacing-3);
        box-shadow: var(--shadow-sm);
    }
    
    [data-testid="stChatMessageContent"] {
        color: var(--text-primary);
    }
    
    /* Modern selectbox */
    [data-baseweb="select"] {
        border-radius: var(--radius);
        margin: var(--spacing-2) 0;
    }
    
    [data-baseweb="select"] > div {
        background-color: var(--bg-white);
        border-color: var(--border-color);
        border-radius: var(--radius);
        padding: var(--spacing-2);
    }
    
    /* Modern checkbox */
    [data-testid="stCheckbox"] {
        margin: var(--spacing-2) 0;
    }
    
    [data-testid="stCheckbox"] > div > div {
        background-color: var(--primary);
        border-radius: var(--radius-sm);
    }
    
    /* Modern caption text */
    .stCaption {
        color: var(--text-secondary);
        font-size: 0.9rem;
        margin-top: var(--spacing-1);
    }
    
    /* Animations */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .animate-fade-in {
        animation: fadeIn 0.5s ease-out;
    }
    
    /* Add animation to main elements */
    .main-header, .description, .card-container {
        animation: fadeIn 0.5s ease-out;
    }
    
    /* Column layout improvements */
    .row-widget.stHorizontal {
        gap: var(--spacing-3);
        margin: var(--spacing-3) 0;
    }
    
    /* Improve spacing for form elements */
    .stForm > div {
        padding: var(--spacing-3) !important;
        background-color: rgba(248, 249, 250, 0.6);
        border-radius: var(--radius);
        margin-bottom: var(--spacing-4) !important;
        border: 1px solid var(--border-color);
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: var(--bg-light);
        padding: var(--spacing-3);
        border-right: 1px solid var(--border-color);
    }
    
    [data-testid="stSidebar"] > div {
        padding: var(--spacing-3);
    }
    
    [data-testid="stSidebar"] h1 {
        color: var(--primary);
        font-size: 1.5rem;
        margin-bottom: var(--spacing-3);
        font-weight: 700;
        border-bottom: 2px solid var(--border-color);
        padding-bottom: var(--spacing-2);
    }
    
    /* Improve spacing for markdown elements */
    [data-testid="stMarkdownContainer"] > p {
        margin: var(--spacing-2) 0;
    }
    
    /* Add visual separation between settings and content areas */
    .main .block-container {
        padding-left: var(--spacing-4) !important;
    }
    
    /* Improve spacing for form elements */
    .stForm > div > div {
        margin-bottom: var(--spacing-3);
    }
    
    /* Enhance selectbox styling */
    .stSelectbox > div > div > div {
        background-color: white;
        border-radius: 8px;
        border: 1px solid var(--border-color);
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        transition: all 0.3s ease;
    }
    
    .stSelectbox > div > div > div:hover {
        border-color: var(--primary-dark);
        box-shadow: 0 2px 5px rgba(0,0,0,0.08);
    }
    
    /* Enhance slider styling */
    .stSlider > div {
        padding-top: var(--spacing-2);
        padding-bottom: var(--spacing-2);
    }
    
    /* Improve checkbox styling */
    .stCheckbox > div {
        padding: var(--spacing-2);
        background-color: rgba(248, 249, 250, 0.4);
        border-radius: var(--radius);
    }
</style>
""", unsafe_allow_html=True)

# Check for required API keys with more detailed messages
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    st.error("OpenAI API key is not configured. Please create a .env file in your project root with OPENAI_API_KEY=your_key_here")
    st.info("You can get an API key from https://platform.openai.com/account/api-keys")
    st.stop()
elif openai_api_key == "your_openai_key_here" or openai_api_key == "your-openai-api-key":
    st.error("Please replace the placeholder with your actual OpenAI API key in the .env file")
    st.info("You can get an API key from https://platform.openai.com/account/api-keys")
    st.stop()

if not (os.getenv("GOOGLE_API_KEY") and os.getenv("GOOGLE_CSE_ID")):
    st.error("Google Search API credentials are not configured. Please check your .env file.")
    st.info("You need both GOOGLE_API_KEY and GOOGLE_CSE_ID in your .env file")
    st.stop()

# Title and description in centered container
st.markdown('<div class="center-content" style="margin-bottom: 0;">', unsafe_allow_html=True)
st.markdown('<div class="main-header">✨ Technical Blog Generator</div>', unsafe_allow_html=True)
st.markdown("""
<div class="description">
    Generate comprehensive technical blog posts with AI assistance. 
    <span style="background: linear-gradient(90deg, #4361EE, #7209B7); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 600;">
        Create accurate, well-researched content with just a few clicks.
    </span>
</div>
""", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# Add a small space after the description
st.markdown('<div style="margin-bottom: 0.5rem;"></div>', unsafe_allow_html=True)

# Add a dark mode toggle in the sidebar
with st.sidebar:
    st.title("Settings")
    
    # Add logout button at the top of the sidebar
    logout_container = st.container()
    with logout_container:
        st.markdown("""
        <style>
        .logout-button {
            margin-bottom: 20px;
            padding-bottom: 20px;
            border-bottom: 1px solid #dee2e6;
        }
        
        /* Style the logout button specifically */
        .logout-section {
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 1px solid #dee2e6;
        }
        </style>
        <div class="logout-button">
        </div>
        """, unsafe_allow_html=True)
        
        # Display user info and logout button
        st.markdown(f"**Logged in as:** {name}")
        
        # Create a dedicated logout button with a unique key and Bootstrap styling
        if st.button("Sign Out", key="sidebar_logout_button"):
            # Call the logout function
            logout()
            # Clear all session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            # Force a rerun to redirect to login page
            st.rerun()
    
    # Apply compact view styling by default
    st.markdown("""
    <style>
        .main-header {
            font-size: 2rem !important;
            margin-bottom: 0.8rem !important;
            padding: 0.5rem !important;
        }
        .description {
            font-size: 0.9rem !important;
            padding: 0.8rem !important;
            margin-bottom: 1rem !important;
        }
        .card-container {
            padding: 1rem !important;
            margin: 0.5rem 0 !important;
        }
        .stButton button {
            padding: 0.4rem 0.8rem !important;
        }
        div.row-widget.stRadio > div {
            flex-direction: row !important;
            align-items: center !important;
        }
        div.row-widget.stRadio > div > label {
            padding: 0.2rem 0.5rem !important;
            margin: 0 0.2rem !important;
        }
        .stTabs [data-baseweb="tab"] {
            padding-top: 0.4rem !important;
            padding-bottom: 0.4rem !important;
        }
        .streamlit-expanderHeader {
            font-size: 0.9rem !important;
            padding: 0.4rem !important;
        }
        /* Reduce spacing between elements */
        .stMarkdown p {
            margin-bottom: 0.5rem !important;
        }
        .element-container {
            margin-bottom: 0.5rem !important;
        }
    </style>
    """, unsafe_allow_html=True)

# Input section in a card-like container
# Removing the card container div
# st.markdown('<div class="card-container">', unsafe_allow_html=True)

# Create columns for a more organized layout
col1, col2 = st.columns(2)

with col1:
    topic = st.text_input("📌 Enter your technical topic:", 
                         placeholder="e.g., Docker containerization",
                         help="Required: The main topic for your blog post")

with col2:
    keywords = st.text_input("🔑 Enter keywords (optional, comma-separated):", 
                            placeholder="e.g., containers, virtualization, microservices",
                            help="Optional: Specific aspects of the topic to focus on")
    st.caption("Leave empty to generate content based on the topic alone")

# Create a row for depth and cache options
col1, col2 = st.columns(2)

with col1:
    # Depth selector with better styling - Fix empty label warning
    st.markdown("### 📊 Content Depth <span style='font-weight:400; color:#6B7280; font-size:0.9rem;'>(Select complexity level)</span>", unsafe_allow_html=True)
    depth = st.select_slider(
        label="Content technical depth level",  # Add a proper label
        options=["beginner", "intermediate", "advanced"],
        value="intermediate",
        label_visibility="collapsed"  # Hide the label but keep it for accessibility
    )
    
    # Add visual indicator for selected complexity level
    complexity_indicators = {
        "beginner": """<div class="complexity-indicator complexity-beginner">Beginner-friendly content</div>""",
        "intermediate": """<div class="complexity-indicator complexity-intermediate">Intermediate complexity</div>""",
        "advanced": """<div class="complexity-indicator complexity-advanced">Advanced technical content</div>"""
    }
    st.markdown(complexity_indicators[depth], unsafe_allow_html=True)

with col2:
    # Add cache control
    st.markdown("### 🔄 Cache Control <span style='font-weight:400; color:#6B7280; font-size:0.9rem;'>(Performance options)</span>", unsafe_allow_html=True)
    use_cache = st.checkbox("Use cached results if available", value=True,
                           help="Faster results, but may not include the latest information")
    if not use_cache:
        st.caption("⚠️ Generating fresh content uses more API credits")

# Add tabs for main content and chat
main_tab, chat_tab = st.tabs(["📝 Blog Generator", "💬 Chat with Research Expert"])

with main_tab:
    # Add a divider
    st.markdown("<hr>", unsafe_allow_html=True)

    # Create a single button and store its state - centered with Bootstrap styling
    st.markdown('<div class="center-content">', unsafe_allow_html=True)
    generate_clicked = st.button("🚀 Generate Content", key="generate_content_button")
    st.markdown('</div>', unsafe_allow_html=True)

    if generate_clicked:
        if topic:
            # Create a simple progress bar without status text
            progress_bar = st.progress(0)
            
            def update_progress(progress_value, status_message):
                """Update the progress bar only."""
                progress_bar.progress(progress_value)
                # No status text or agent indicators
            
            # Use a minimal spinner
            with st.spinner("Generating content..."):
                try:
                    # Convert inputs to ResearchTopic
                    try:
                        # First try to create the ResearchTopic object
                        research_request = ResearchTopic(
                            title=topic,
                            keywords=[k.strip() for k in keywords.split(",") if k.strip()],
                            depth=depth
                        )
                    except ValidationError as ve:
                        # Handle Pydantic validation errors specifically
                        st.error(f"Validation Error: {str(ve)}")
                        st.stop()
                    
                    # Define a simplified progress callback that only updates the progress bar
                    def simplified_progress_callback(progress_value, status_message):
                        # Just update the progress bar, ignore status messages
                        progress_bar.progress(progress_value)
                    
                    # Call research_topic with our simplified callback
                    result = research_topic(research_request, progress_callback=simplified_progress_callback, use_cache=use_cache)
                    
                    # Check for errors
                    if "error" in result:
                        st.error(f"Error: {result['error']}")
                        if "OpenAI API key not set" in result["error"]:
                            st.info("Please add your OpenAI API key to the .env file in your project root")
                        st.stop()
                    
                    # Clear the progress indicator
                    progress_bar.empty()
                    
                    # Store the generated content in session state for access in the chat tab
                    if "current_blog_title" not in st.session_state:
                        st.session_state.current_blog_title = result['title']
                    if "current_blog_content" not in st.session_state:
                        st.session_state.current_blog_content = result['content']
                    else:
                        st.session_state.current_blog_title = result['title']
                        st.session_state.current_blog_content = result['content']
                    
                    # Display results in a card container
                    st.markdown('<div class="card-container">', unsafe_allow_html=True)
                    
                    # Display the results
                    if "error" in result:
                        st.error(f"Error: {result['error']}")
                    else:
                        with st.container():
                            st.markdown("## 📝 Generated Blog Post")
                            
                            # Display cache information with more details
                            if result.get("source") == "cached":
                                st.markdown(
                                    f"""
                                    <div class="cache-box">
                                        ♻️ Content retrieved from cache
                                        <div class="cache-details">
                                            <small>Originally generated: {result.get("cached_at", "unknown time")}</small>
                                        </div>
                                    </div>
                                    """, 
                                    unsafe_allow_html=True
                                )
                            else:
                                st.success("✅ New content generated successfully!")
                            
                            # Display metadata in an expander
                            with st.expander("Content Metadata"):
                                st.markdown(f"**Title:** {result['title']}")
                                st.markdown(f"**Depth:** {result['depth']}")
                                st.markdown(f"**Keywords:** {', '.join(result['keywords']) if result['keywords'] else 'None'}")
                                st.markdown(f"**Source:** {'Retrieved from cache' if result.get('source') == 'cached' else 'Freshly generated'}")
                                if result.get("source") == "cached":
                                    st.markdown(f"**Cache Key:** `{result.get('cache_key', 'N/A')}`")
                                    st.markdown(f"**Cached At:** {result.get('cached_at', 'unknown time')}")
                                else:
                                    st.markdown(f"**Generated At:** {result.get('generated_at', 'N/A')}")
                    
                    # Create a text area for editing the generated content
                    generated_content = result["content"]
                    st.markdown(f"# {result['title']}")
                    
                    # Create tabs for editing and preview
                    edit_tab, preview_tab = st.tabs(["✏️ Edit", "👁️ Preview"])
                    
                    with edit_tab:
                        edited_content = st.text_area(
                            "Edit your blog post",
                            value=generated_content,
                            height=400,
                            key="blog_editor"
                        )
                        
                        # Update the session state with edited content
                        st.session_state.current_blog_content = edited_content
                    
                    with preview_tab:
                        st.markdown("### Preview of Formatted Blog Post")
                        
                        # Display the content as formatted markdown only
                        st.code(edited_content, language="markdown")
                    
                    # Center the download button
                    st.markdown('<div class="center-content">', unsafe_allow_html=True)
                    
                    # Function to convert markdown to HTML
                    def markdown_to_html(md_text, title):
                        html_content = markdown.markdown(md_text, extensions=['fenced_code', 'tables'])
                        
                        # Create a complete HTML document with basic styling
                        html_doc = f"""<!DOCTYPE html>
                        <html>
                        <head>
                            <title>{title}</title>
                            <meta charset="utf-8">
                            <meta name="viewport" content="width=device-width, initial-scale=1">
                            <style>
                                body {{
                                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                                    line-height: 1.6;
                                    color: #333;
                                    max-width: 800px;
                                    margin: 0 auto;
                                    padding: 20px;
                                }}
                                h1, h2, h3, h4, h5, h6 {{
                                    color: #0066cc;
                                    margin-top: 24px;
                                    margin-bottom: 16px;
                                }}
                                h1 {{
                                    font-size: 2em;
                                    border-bottom: 1px solid #eaecef;
                                    padding-bottom: 0.3em;
                                }}
                                h2 {{
                                    font-size: 1.5em;
                                    border-bottom: 1px solid #eaecef;
                                    padding-bottom: 0.3em;
                                }}
                                code {{
                                    background-color: #f6f8fa;
                                    border-radius: 3px;
                                    font-family: SFMono-Regular, Consolas, "Liberation Mono", Menlo, monospace;
                                    padding: 0.2em 0.4em;
                                    font-size: 85%;
                                }}
                                pre {{
                                    background-color: #f6f8fa;
                                    border-radius: 3px;
                                    font-family: SFMono-Regular, Consolas, "Liberation Mono", Menlo, monospace;
                                    padding: 16px;
                                    overflow: auto;
                                }}
                                pre code {{
                                    background-color: transparent;
                                    padding: 0;
                                }}
                                blockquote {{
                                    border-left: 4px solid #ddd;
                                    padding-left: 16px;
                                    color: #666;
                                    margin-left: 0;
                                }}
                                img {{
                                    max-width: 100%;
                                }}
                                table {{
                                    border-collapse: collapse;
                                    width: 100%;
                                    margin-bottom: 16px;
                                }}
                                table, th, td {{
                                    border: 1px solid #ddd;
                                }}
                                th, td {{
                                    padding: 8px 16px;
                                    text-align: left;
                                }}
                                th {{
                                    background-color: #f6f8fa;
                                }}
                            </style>
                        </head>
                        <body>
                            <h1>{title}</h1>
                            {html_content}
                        </body>
                        </html>"""
                        
                        return html_doc
                    
                    # Create HTML version of the content
                    html_content = markdown_to_html(edited_content, result['title'])
                    
                    # Create a row for download buttons
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Markdown download button
                        st.download_button(
                            label="📥 Download as Markdown",
                            data=edited_content,
                            file_name=f"{topic.lower().replace(' ', '_')}_blog.md",
                            mime="text/markdown",
                            help="Download your blog post as a Markdown file"
                        )
                    
                    with col2:
                        # HTML download button
                        st.download_button(
                            label="📄 Download as HTML",
                            data=html_content,
                            file_name=f"{topic.lower().replace(' ', '_')}_blog.html",
                            mime="text/html",
                            help="Download your blog post as an HTML file"
                        )
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Add some tips
                    with st.expander("✨ Tips for editing your blog post"):
                        st.markdown("""
                        - Add personal insights and experiences
                        - Check code examples for accuracy
                        - Add more examples or use cases
                        - Include images or diagrams (add image links)
                        - Format with markdown for better readability
                        """)
                    
                    st.markdown('</div>', unsafe_allow_html=True)  # Close card container
                    
                    # Save the blog to the local database
                    blog_id = save_blog(result['title'], edited_content, result['metadata'])
                    
                except Exception as e:
                    # This is for other unexpected errors - keep this as it's important for debugging
                    st.error(f"Error generating content: {str(e)}")
                    # Only show API key message if it's likely an API issue
                    if "api" in str(e).lower() or "key" in str(e).lower() or "openai" in str(e).lower():
                        st.info("This appears to be an API key error. Please check that your OpenAI API key is valid and has sufficient credits.")
        else:
            st.error("Please provide a topic")

with chat_tab:
    # Import the chat agents
    from app.agents.chat_agents import get_agent_response
    
    st.markdown("## 💬 Chat with Research Expert")
    
    # Check if a blog has been generated
    if "current_blog_content" not in st.session_state:
        st.markdown("""
        <div style="background-color: #EFF6FF; padding: 20px; border-radius: 12px; border-left: 5px solid #3B82F6; margin: 20px 0;">
            <h3 style="margin-top: 0; color: #2563EB; font-size: 1.1rem;">✨ Getting Started</h3>
            <p style="margin-bottom: 0;">Generate a blog post first to chat with experts about it!</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="background-color: #ECFDF5; padding: 15px; border-radius: 12px; border-left: 5px solid #10B981; margin-bottom: 20px;">
            <h3 style="margin-top: 0; color: #059669; font-size: 1.1rem;">📄 Currently discussing</h3>
            <p style="margin-bottom: 0; font-weight: 500;">{st.session_state.current_blog_title}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Initialize chat messages if not already done
        if "messages" not in st.session_state:
            st.session_state.messages = []
            
        # Initialize a key for the chat input
        if "chat_input_key" not in st.session_state:
            st.session_state.chat_input_key = 0
        
        # Define agent options and set Research Expert as default
        agent_options = ["Research Expert", "Content Editor", "Technical Reviewer", "SEO Specialist"]
        default_agent = "Research Expert"
        
        # Display agent descriptions
        agent_descriptions = {
            "Research Expert": "Finds accurate information and answers questions about technical topics.",
            "Content Editor": "Improves clarity, structure, and readability of your content.",
            "Technical Reviewer": "Ensures technical accuracy and suggests best practices.",
            "SEO Specialist": "Optimizes content for search engines and suggests keywords."
        }
        
        agent_icons = {
            "Research Expert": "🔍",
            "Content Editor": "✏️",
            "Technical Reviewer": "🛠️",
            "SEO Specialist": "📈"
        }
        
        # Display Research Expert description
        st.markdown(f"""
        <div style="background-color: #F8FAFC; padding: 10px 15px; border-radius: 8px; border-left: 3px solid #4361EE; margin-bottom: 15px;">
            <p style="margin: 0; font-size: 0.95rem;"><strong>{agent_icons[default_agent]} {default_agent}:</strong> {agent_descriptions[default_agent]}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"], avatar=message.get("avatar", None)):
                st.markdown(message["content"])
        
        # Add a button to clear chat history with improved styling
        st.markdown("<div style='display: flex; justify-content: center; margin-top: 20px;'>", unsafe_allow_html=True)
        if st.button("🗑️ Clear Chat History", type="secondary"):
            st.session_state.messages = []
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Use Streamlit's native chat_input which appears at the bottom
        if prompt := st.chat_input("Ask the Research Expert a question...", key=f"chat_input_{st.session_state.chat_input_key}"):
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Display user message
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Get response from Research Expert
            with st.chat_message("assistant", avatar=agent_icons[default_agent]):
                with st.spinner(f"Consulting {default_agent}..."):
                    response = get_agent_response(
                        default_agent, 
                        prompt, 
                        st.session_state.current_blog_content
                    )
                    st.markdown(response)
            
            # Add assistant response to chat history
            st.session_state.messages.append({
                "role": "assistant", 
                "content": response,
                "avatar": agent_icons[default_agent]
            })
            
            # Increment the key to create a new input widget on next rerun
            st.session_state.chat_input_key += 1
            st.rerun() 