import streamlit as st
import markdown

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

# Configure the app - MUST be the first Streamlit command
st.set_page_config(
    page_title="TechMuse",
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
import base64
import uuid
from pathlib import Path
import time
import re

# Load environment variables
load_dotenv()

# Add an environment variable to indicate we're in a Streamlit deployment
if "STREAMLIT_RUNTIME_ENVIRONMENT" in os.environ:
    os.environ["STREAMLIT_DEPLOYMENT"] = "1"

# Check if running on Streamlit Cloud
if os.getenv("STREAMLIT_RUNTIME_ENVIRONMENT") == "cloud":
    os.environ["STREAMLIT_DEPLOYMENT"] = "1"
    print("Running on Streamlit Cloud - Setting STREAMLIT_DEPLOYMENT=1")

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

# Initialize all session state variables
if 'content_generated' not in st.session_state:
    st.session_state.content_generated = False
if 'current_result' not in st.session_state:
    st.session_state.current_result = None
if 'edited_content' not in st.session_state:
    st.session_state.edited_content = ""
if 'current_blog_content' not in st.session_state:
    st.session_state.current_blog_content = ""
if 'current_blog_title' not in st.session_state:
    st.session_state.current_blog_title = ""

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
        background-image: url("data:image/svg+xml,%3Csvg width='100' height='100' viewBox='0 0 100 100' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M11 18c3.866 0 7-3.134 7-7s-3.134-7-7-7-7 3.134-7 7 3.134 7 7 7zm48 25c3.866 0 7-3.134 7-7s-3.134-7-7-7-7 3.134-7 7 3.134 7 7 7zm-43-7c1.657 0 3-1.343 3-3s-.895-3-2-3-3 .895-3 2 .895 3 2 3zm63 31c1.657 0 3-1.343 3-3s-.895-3-2-3-3 .895-3 2 .895 3 2 3zM34 90c1.657 0 3-1.343 3-3s-.895-3-2-3-3 .895-3 2 .895 3 2 3zm56-76c1.657 0 3-1.343 3-3s-.895-3-2-3-3 .895-3 2 .895 3 2 3zM12 86c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm28-65c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm23-11c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zm-6 60c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm29 22c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zM32 63c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zm57-13c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zm-9-21c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2zM60 91c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2zM35 41c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2zM12 60c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2z' fill='%23e0e0e0' fill-opacity='0.1' fill-rule='evenodd'/%3E%3C/svg%3E");
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
        from { opacity: 0; transform: scale(1); }
        to { opacity: 1; transform: scale(40); }
    }
    
    /* Sign out button specific styling */
    .stButton button[data-testid="baseButton-secondary"]:has(div:contains("Sign Out")) {
        background-color: #f8f9fa;
        color: #6c757d;
        border: 1px solid #dee2e6;
        border-radius: 6px;
        padding: 0.3rem 0.6rem;
        font-size: 0.85rem;
        font-weight: 500;
        transition: all 0.2s ease;
        box-shadow: none;
        width: auto !important;
        height: auto !important;
    }
    
    .stButton button[data-testid="baseButton-secondary"]:has(div:contains("Sign Out")):hover {
        background-color: #e9ecef;
        color: #495057;
        transform: translateY(-1px);
    }
    
    /* Generate content button - make it stand out with accent color */
    .stButton button[data-testid="baseButton-primary"]:has(div:contains("Generate Content")) {
        background: linear-gradient(90deg, #4361EE, #7209B7);
        color: white;
        border: none;
        border-radius: 6px;
        padding: 0.4rem 0.8rem;
        font-size: 0.9rem;
        font-weight: 500;
        transition: all 0.2s ease;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    
    .stButton button[data-testid="baseButton-primary"]:has(div:contains("Generate Content")):hover {
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        transform: translateY(-1px);
    }
    
    /* Modern download button */
    .stDownloadButton button {
        background-color: var(--primary);
        color: white;
        font-weight: 500;
        border-radius: 8px;
        box-shadow: var(--shadow-sm);
        width: 100% !important;
        height: 48px !important;
        margin: var(--spacing-2) auto !important;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.2s ease;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-size: 0.9rem;
    }
    
    .stDownloadButton button:hover {
        background-color: #3651d4;
        box-shadow: var(--shadow);
        transform: translateY(-2px);
    }
    
    .stDownloadButton button:active {
        transform: translateY(0);
        box-shadow: var(--shadow-sm);
    }
    
    /* Different colors for different download buttons */
    .markdown-download button {
        background: linear-gradient(90deg, #4361EE, #3A0CA3);
    }
    
    .markdown-download button:hover {
        background: linear-gradient(90deg, #3651d4, #2f0a82);
    }
    
    .html-download button {
        background: linear-gradient(90deg, #7209B7, #560BAD);
    }
    
    .html-download button:hover {
        background: linear-gradient(90deg, #5c07a3, #4a099a);
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
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
    
    @keyframes shimmer {
        0% { background-position: -1000px 0; }
        100% { background-position: 1000px 0; }
    }
    
    .animate-fade-in {
        animation: fadeIn 0.5s ease-out;
    }
    
    .animate-pulse {
        animation: pulse 2s infinite ease-in-out;
    }
    
    /* Add animation to main elements */
    .main-header, .description, .card-container {
        animation: fadeIn 0.5s ease-out;
    }
    
    /* Tab transition animations */
    .stTabs [data-baseweb="tab-panel"] {
        animation: fadeIn 0.3s ease-out;
    }
    
    /* Loading animation */
    .loading-animation {
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 20px 0;
        padding: 20px;
        background-color: var(--bg-light);
        border-radius: var(--radius);
        box-shadow: var(--shadow-sm);
    }
    
    .loading-animation .dot {
        width: 12px;
        height: 12px;
        margin: 0 5px;
        background-color: var(--primary);
        border-radius: 50%;
        display: inline-block;
        animation: dot-pulse 1.5s infinite ease-in-out;
    }
    
    .loading-animation .dot:nth-child(1) {
        animation-delay: 0s;
    }
    
    .loading-animation .dot:nth-child(2) {
        animation-delay: 0.3s;
        background-color: var(--accent);
    }
    
    .loading-animation .dot:nth-child(3) {
        animation-delay: 0.6s;
        background-color: var(--success);
    }
    
    @keyframes dot-pulse {
        0%, 80%, 100% { transform: scale(0); opacity: 0.5; }
        40% { transform: scale(1); opacity: 1; }
    }
    
    /* Shimmer effect for loading states */
    .shimmer {
        background: linear-gradient(90deg, 
            rgba(255,255,255,0) 0%, 
            rgba(255,255,255,0.6) 50%, 
            rgba(255,255,255,0) 100%);
        background-size: 1000px 100%;
        animation: shimmer 2s infinite linear;
    }
    
    /* Progress indicator styling */
    .progress-container {
        margin: 20px 0;
        padding: 15px;
        background-color: var(--bg-light);
        border-radius: var(--radius);
        box-shadow: var(--shadow-sm);
        text-align: center;
    }
    
    .progress-label {
        display: block;
        margin-bottom: 10px;
        font-weight: 500;
        color: var(--text-primary);
    }
    
    .progress-steps {
        display: flex;
        justify-content: space-between;
        margin-top: 10px;
    }
    
    .progress-step {
        flex: 1;
        text-align: center;
        position: relative;
        font-size: 0.8rem;
        color: var(--text-secondary);
    }
    
    .progress-step.active {
        color: var(--primary);
        font-weight: 600;
    }
    
    .progress-step.completed {
        color: var(--success);
    }
    
    .progress-step:before {
        content: "";
        width: 20px;
        height: 20px;
        background-color: var(--bg-light);
        border: 2px solid var(--border-color);
        border-radius: 50%;
        display: block;
        margin: 0 auto 5px;
    }
    
    .progress-step.active:before {
        background-color: var(--primary);
        border-color: var(--primary);
        box-shadow: 0 0 0 3px rgba(13, 110, 253, 0.2);
    }
    
    .progress-step.completed:before {
        background-color: var(--success);
        border-color: var(--success);
    }
    
    /* Responsive design improvements */
    @media (max-width: 992px) {
        .main-header {
            font-size: 2.2rem !important;
        }
        
        .description {
            font-size: 1rem !important;
            max-width: 100% !important;
        }
        
        .stButton button {
            width: 180px !important;
        }
        
        button[key="generate_content_button"] {
            width: 200px !important;
        }
        
        .card-container {
            padding: var(--spacing-3) !important;
        }
    }
    
    @media (max-width: 768px) {
        .main-header {
            font-size: 1.8rem !important;
            padding: var(--spacing-2) !important;
        }
        
        .description {
            font-size: 0.9rem !important;
            padding: var(--spacing-2) !important;
        }
        
        [data-testid="stMarkdownContainer"] h3 {
            font-size: 1.2rem !important;
        }
        
        .stButton button {
            width: 100% !important;
            max-width: 160px !important;
        }
        
        button[key="generate_content_button"] {
            width: 180px !important;
        }
        
        .stDownloadButton button {
            width: 100% !important;
            max-width: 160px !important;
        }
        
        /* Adjust column layout for mobile */
        [data-testid="column"] {
            width: 100% !important;
            flex: 1 1 100% !important;
            min-width: 100% !important;
        }
        
        /* Stack columns on mobile */
        [data-testid="stHorizontalBlock"] {
            flex-direction: column !important;
        }
        
        /* Adjust tab padding */
        .stTabs [data-baseweb="tab"] {
            padding: var(--spacing-1) var(--spacing-2) !important;
        }
    }
    
    @media (max-width: 576px) {
        .main-header {
            font-size: 1.5rem !important;
        }
        
        .description {
            font-size: 0.85rem !important;
        }
        
        /* Make sidebar full width on very small screens */
        [data-testid="stSidebar"] {
            width: 100% !important;
            min-width: 100% !important;
        }
    }

    /* Add specific styles for iPhone SE and other small devices */
    @media (max-width: 375px) {
        /* Reduce overall padding */
        .block-container {
            padding: var(--spacing-2) !important;
        }
        
        /* Make main header smaller */
        .main-header {
            font-size: 1.3rem !important;
            padding: var(--spacing-1) !important;
            margin-bottom: var(--spacing-2) !important;
        }
        
        /* Reduce description size */
        .description {
            font-size: 0.8rem !important;
            padding: var(--spacing-1) !important;
        }
        
        /* Make buttons smaller but still usable */
        .stButton button {
            width: 100% !important;
            max-width: 140px !important;
            height: 38px !important;
            font-size: 0.9rem !important;
            padding: 4px 8px !important;
        }
        
        button[key="generate_content_button"] {
            width: 160px !important;
            height: 42px !important;
        }
        
        /* Adjust input fields for better mobile experience */
        input[type="text"], textarea {
            font-size: 16px !important; /* Prevents iOS zoom on focus */
        }
        
        /* Make expert buttons stack vertically on iPhone SE */
        [data-testid="column"] {
            min-width: 100% !important;
            margin-bottom: var(--spacing-1) !important;
        }
        
        /* Adjust expert buttons container */
        .agent-selector-container {
            flex-direction: column !important;
        }
        
        /* Make tabs more compact */
        .stTabs [data-baseweb="tab"] {
            padding: 4px 8px !important;
            font-size: 0.85rem !important;
        }
        
        /* Reduce section header size */
        [data-testid="stMarkdownContainer"] h3 {
            font-size: 1rem !important;
        }
        
        /* Adjust chat interface for small screens */
        [data-testid="stChatMessage"] {
            padding: var(--spacing-2) !important;
            margin-bottom: var(--spacing-2) !important;
        }
        
        /* Make text areas smaller */
        .stTextArea textarea {
            min-height: 200px !important;
        }
    }
    
    /* Style for the agent selector container */
    .agent-selector-container {
        margin-bottom: 20px;
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    
    /* Style for the agent selector title */
    .agent-selector-title {
        font-weight: 500;
        margin-bottom: 10px;
        color: var(--text-primary);
    }
    
    /* Hide the default radio button appearance */
    div.row-widget.stRadio > div {
        flex-direction: column !important;
        gap: 0 !important;
    }
    
    div.row-widget.stRadio > div > label {
        padding: 12px 15px !important;
        cursor: pointer !important;
        border-bottom: 1px solid #e9ecef !important;
        margin: 0 !important;
        transition: all 0.2s ease !important;
        background-color: white !important;
        position: relative !important;
        display: flex !important;
        align-items: center !important;
    }
    
    div.row-widget.stRadio > div > label:hover {
        background-color: #f8f9fa !important;
    }
    
    div.row-widget.stRadio > div > label:first-child {
        border-top-left-radius: 8px !important;
        border-top-right-radius: 8px !important;
    }
    
    div.row-widget.stRadio > div > label:last-child {
        border-bottom-left-radius: 8px !important;
        border-bottom-right-radius: 8px !important;
        border-bottom: none !important;
    }
    
    div.row-widget.stRadio > div > label[data-baseweb="radio"] > div:first-child {
        background-color: white !important;
        border-color: #0d6efd !important;
    }
    
    div.row-widget.stRadio > div > label[data-baseweb="radio"] > div:first-child div {
        background-color: #0d6efd !important;
        border-color: #0d6efd !important;
    }
    
    /* Add icons to the radio options */
    div.row-widget.stRadio > div > label[data-baseweb="radio"] > div:last-child::before {
        margin-right: 10px;
        font-size: 18px;
    }
    
    /* Selected state styling */
    div.row-widget.stRadio > div > label[aria-checked="true"] {
        background-color: #e9f2ff !important;
        font-weight: 600 !important;
        border-left: 4px solid #0d6efd !important;
    }

    /* Change the Welcome text to TechMuse */
    h1:contains("Welcome") {
        font-size: 0;  /* Hide the original text */
    }

    h1:contains("Welcome")::after {
        content: "✨ TechMuse";
        font-size: 2.2rem;  /* Restore font size for new text */
        font-weight: 700;
        color: var(--primary);
    }
    /* Reduce space between title and agent buttons */
.agent-selector-title {
    font-weight: 500;
    margin-bottom: 5px !important; /* Reduced from 10px */
    color: var(--text-primary);
}

/* Ensure the container doesn't add extra space */
.agent-selector-container {
    margin-top: 0 !important;
    margin-bottom: 15px !important; /* Reduced from 20px */
}

/* Remove any extra padding that might be added by Streamlit */
[data-testid="stVerticalBlock"] > div:has(.agent-selector-title) {
    margin-bottom: 0 !important;
    padding-bottom: 0 !important;
}

/* Target the specific gap between title and buttons */
.agent-selector-title + div {
    margin-top: 5px !important;
}

/* Make sure the expert buttons container doesn't have extra space */
.expert-buttons-container {
    margin-top: 0 !important;
}

    /* Modern expert tabs */
    .expert-buttons-container {
        margin-bottom: 1rem;
    }
    
    .expert-buttons-container .stButton button {
        border-radius: 6px;
        padding: 0.3rem 0.5rem;
        font-size: 0.85rem;
        font-weight: 500;
        transition: all 0.2s ease;
        box-shadow: none;
    }
    
    .expert-buttons-container .stButton button[data-testid="baseButton-primary"] {
        background: linear-gradient(90deg, #4361EE, #3B82F6);
        border: none;
    }
    
    .expert-buttons-container .stButton button[data-testid="baseButton-secondary"] {
        background-color: #f8f9fa;
        color: #4B5563;
        border: 1px solid #E5E7EB;
    }
    
    .expert-buttons-container .stButton button:hover {
        transform: translateY(-1px);
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Clear chat history button */
    .stButton button[data-testid="baseButton-secondary"]:has(div:contains("Clear Chat History")) {
        background-color: #f8f9fa;
        color: #6c757d;
        border: 1px solid #dee2e6;
        border-radius: 6px;
        padding: 0.3rem 0.6rem;
        font-size: 0.85rem;
        font-weight: 500;
        transition: all 0.2s ease;
        box-shadow: none;
    }
    
    /* Make tabs more modern */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        padding: 0.5rem 1rem !important;
        font-size: 0.9rem;
        font-weight: 500;
        border-radius: 6px 6px 0 0;
    }
    
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background-color: #f0f7ff;
        border-bottom: 2px solid #3B82F6;
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
st.markdown('<div class="main-header">✨ TechMuse</div>', unsafe_allow_html=True)
st.markdown("""
<div class="description">
    <span style="background: linear-gradient(90deg, #4361EE, #7209B7); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 600;">
        Create accurate, well-researched content with just a few clicks.
    </span>
</div>
""", unsafe_allow_html=True)

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
        st.markdown(f"""
        <div style="display: flex; align-items: center; margin-bottom: 15px;">
            <div style="background-color: #4361EE; color: white; width: 32px; height: 32px; border-radius: 50%; 
                 display: flex; align-items: center; justify-content: center; margin-right: 10px; font-weight: bold;">
                {name[0].upper()}
            </div>
            <div>
                <div style="font-weight: 500;">{name}</div>
                <div style="font-size: 0.8rem; color: #6c757d;">{username}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Create a dedicated logout button with a unique key and Bootstrap styling
        if st.button("🚪 Sign Out", key="sidebar_logout_button"):
            # Call the logout function
            logout()
            # Clear all session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            # Force a rerun to redirect to login page
            st.rerun()
            
        # Add admin page link for admin users
        from app.auth import authenticator
        if authenticator.is_admin(username):
            if st.button("👑 Admin Dashboard", key="admin_dashboard_button"):
                st.session_state.show_admin = True
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

# Check if we should show the admin page
if "show_admin" in st.session_state and st.session_state.show_admin:
    authenticator.show_admin_page()
    # Add a back button
    if st.button("← Back to App", key="back_to_app_button"):
        st.session_state.show_admin = False
        st.rerun()
    st.stop()

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

with col2:
    # Add cache control
    st.markdown("### 🔄 Cache Control <span style='font-weight:400; color:#6B7280; font-size:0.9rem;'>(Performance options)</span>", unsafe_allow_html=True)
    use_cache = st.checkbox("Use cached results if available", value=True,
                           help="Faster results, but may not include the latest information")
    if not use_cache:
        st.caption("⚠️ Generating fresh content uses more API credits")

# Add tabs for main content and chat
main_tab, chat_tab = st.tabs(["📝 Blog Generator", "💬 Chat with Experts"])

with main_tab:
    # Add a divider
    st.markdown("<hr>", unsafe_allow_html=True)

    # Create a single button and store its state
    st.markdown('<div class="center-content">', unsafe_allow_html=True)
    generate_clicked = st.button("🚀 Generate Content", key="generate_content_button")
    st.markdown('</div>', unsafe_allow_html=True)

    # Check if we should display content
    if generate_clicked or st.session_state.content_generated:
        if topic:
            # Only run the generation process if the button was just clicked
            if generate_clicked:
                # Create a simple progress bar without status text
                progress_bar = st.progress(0)

                # Add a custom loading animation
                loading_container = st.empty()
                loading_container.markdown("""
                <div class="loading-animation">
                    <div class="dot"></div>
                    <div class="dot"></div>
                    <div class="dot"></div>
                    <div style="margin-left: 10px; font-weight: 500;">Generating your content...</div>
                </div>
                """, unsafe_allow_html=True)

                # Add a progress steps indicator
                progress_steps_container = st.empty()
                progress_steps_container.markdown("""
                <div class="progress-container">
                    <span class="progress-label">Content Generation Progress</span>
                    <div class="progress-steps">
                        <div class="progress-step active">Research</div>
                        <div class="progress-step">Outline</div>
                        <div class="progress-step">Draft</div>
                        <div class="progress-step">Finalize</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Now define the update_progress function
                def update_progress(progress_value, status_message):
                    """Update the progress bar and progress steps."""
                    progress_bar.progress(progress_value)
                    
                    # Only add delay for specific transition points to reduce overall generation time
                    # while still making transitions visible
                    if progress_value in [0.25, 0.5, 0.75, 0.95]:
                        time.sleep(1.0)  # Only delay at key transition points
                    
                    # Update progress steps based on progress value with clearer thresholds
                    if progress_value <= 0.25:
                        step_html = """
                        <div class="progress-container">
                            <span class="progress-label">Content Generation Progress</span>
                            <div class="progress-steps">
                                <div class="progress-step active">Research</div>
                                <div class="progress-step">Outline</div>
                                <div class="progress-step">Draft</div>
                                <div class="progress-step">Finalize</div>
                            </div>
                        </div>
                        """
                        loading_message = "Researching your topic..."
                    elif progress_value <= 0.5:
                        step_html = """
                        <div class="progress-container">
                            <span class="progress-label">Content Generation Progress</span>
                            <div class="progress-steps">
                                <div class="progress-step completed">Research</div>
                                <div class="progress-step active">Outline</div>
                                <div class="progress-step">Draft</div>
                                <div class="progress-step">Finalize</div>
                            </div>
                        </div>
                        """
                        loading_message = "Creating content outline..."
                    elif progress_value <= 0.75:
                        step_html = """
                        <div class="progress-container">
                            <span class="progress-label">Content Generation Progress</span>
                            <div class="progress-steps">
                                <div class="progress-step completed">Research</div>
                                <div class="progress-step completed">Outline</div>
                                <div class="progress-step active">Draft</div>
                                <div class="progress-step">Finalize</div>
                            </div>
                        </div>
                        """
                        loading_message = "Drafting your blog post..."
                    else:
                        step_html = """
                        <div class="progress-container">
                            <span class="progress-label">Content Generation Progress</span>
                            <div class="progress-steps">
                                <div class="progress-step completed">Research</div>
                                <div class="progress-step completed">Outline</div>
                                <div class="progress-step completed">Draft</div>
                                <div class="progress-step active">Finalize</div>
                            </div>
                        </div>
                        """
                        loading_message = "Finalizing and polishing content..."
                    
                    # Update the progress steps container
                    progress_steps_container.markdown(step_html, unsafe_allow_html=True)
                    
                    # Also update the loading message based on the current step
                    loading_container.markdown(f"""
                    <div class="loading-animation">
                        <div class="dot"></div>
                        <div class="dot"></div>
                        <div class="dot"></div>
                        <div style="margin-left: 10px; font-weight: 500;">{loading_message}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Create the research request
                try:
                    research_request = ResearchTopic(
                        title=topic,
                        keywords=[k.strip() for k in keywords.split(",") if k.strip()],
                        depth=depth
                    )
                    
                    # Generate content
                    result = research_topic(research_request, progress_callback=update_progress, use_cache=use_cache)
                    
                    # Store everything in session state
                    if "error" not in result:
                        st.session_state.current_result = result
                        st.session_state.edited_content = result["content"]
                        st.session_state.current_blog_content = result["content"]
                        st.session_state.current_blog_title = result["title"]
                        st.session_state.content_generated = True
                        
                        # Clear the progress indicators
                        progress_bar.empty()
                        loading_container.empty()
                        progress_steps_container.empty()
                except Exception as e:
                    st.error(f"Error generating content: {str(e)}")
                    st.stop()
            else:
                # We're displaying previously generated content
                # Make sure we have content to display
                if st.session_state.current_result is None:
                    st.error("No content available. Please generate content first.")
                    st.stop()
                
                # Use the stored result
                result = st.session_state.current_result
            
            # Make sure any lingering progress indicators are cleared
            if 'progress_bar' in locals():
                progress_bar.empty()
            if 'loading_container' in locals():
                loading_container.empty()
            if 'progress_steps_container' in locals():
                progress_steps_container.empty()
            
            # Display success message
            st.markdown("""
            <div style="display: flex; align-items: center; justify-content: center; margin: 20px 0; padding: 15px; background-color: #d1e7dd; border-radius: 8px; animation: fadeIn 0.5s ease-out;">
                <div style="font-size: 24px; margin-right: 10px;">✅</div>
                <div style="font-weight: 600; color: #0f5132;">Content successfully generated!</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Display the blog content
            st.markdown('<div class="card-container">', unsafe_allow_html=True)
            
            with st.container():
                st.markdown("## 📝 Generated Blog Post")
                
                # Display metadata in an expander
                with st.expander("Content Metadata"):
                    st.markdown(f"**Title:** {st.session_state.current_blog_title}")
                    st.markdown(f"**Depth:** {result['depth']}")
                    st.markdown(f"**Keywords:** {', '.join(result['keywords']) if result['keywords'] else 'None'}")
                    # ... other metadata
            
            # Display the title
            st.markdown(f"# {st.session_state.current_blog_title}")
            
            # Create tabs for editing and preview
            edit_tab, preview_tab = st.tabs(["✏️ Edit", "👁️ Preview"])
            
            with edit_tab:
                # Use session state for the text area
                edited_content = st.text_area(
                    "Edit your blog post",
                    value=st.session_state.edited_content,
                    height=400,
                    key="blog_editor"
                )
                
                # Update session state when content changes
                st.session_state.edited_content = edited_content
                st.session_state.current_blog_content = edited_content
            
            with preview_tab:
                st.markdown("### Preview of Formatted Blog Post")
                st.code(st.session_state.edited_content, language="markdown")
            
            # Center the download buttons
            st.markdown('<div class="center-content">', unsafe_allow_html=True)
            
            # Create HTML version of the content from session state
            html_content = markdown_to_html(st.session_state.edited_content, st.session_state.current_blog_title)
            
            # Create a row for download buttons
            col1, col2 = st.columns(2)
            
            with col1:
                # Markdown download button with custom styling
                with st.container():
                    st.markdown('<div class="markdown-download">', unsafe_allow_html=True)
                    st.download_button(
                        label="📥 Download as Markdown",
                        data=st.session_state.edited_content,
                        file_name=f"{topic.lower().replace(' ', '_')}_blog.md",
                        mime="text/markdown",
                        help="Download your blog post as a Markdown file",
                        on_click=lambda: None  # Empty callback to prevent state reset
                    )
                    st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                # HTML download button with custom styling
                with st.container():
                    st.markdown('<div class="html-download">', unsafe_allow_html=True)
                    st.download_button(
                        label="📄 Download as HTML",
                        data=html_content,
                        file_name=f"{topic.lower().replace(' ', '_')}_blog.html",
                        mime="text/html",
                        help="Download your blog post as an HTML file",
                        on_click=lambda: None  # Empty callback to prevent state reset
                    )
                    st.markdown('</div>', unsafe_allow_html=True)
            
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
            blog_id = save_blog(result['title'], result['content'], result['metadata'])
            
        else:
            st.error("Please provide a topic")

with chat_tab:
    # Import the chat agents
    from app.agents.chat_agents import get_agent_response
    
    st.markdown("## 💬 Chat with Experts")
    
    # Check if a blog has been generated
    if "current_blog_content" not in st.session_state:
        st.markdown("""
        <div style="background-color: #EFF6FF; padding: 20px; border-radius: 12px; border-left: 5px solid #3B82F6; margin: 20px 0;">
            <h3 style="margin-top: 0; color: #2563EB; font-size: 1.1rem;">✨ Getting Started</h3>
            <p style="margin: 0; font-size: 0.95rem;">Generate a blog post first to chat with experts about it!</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="background-color: #ECFDF5; padding: 10px 15px; border-radius: 8px; border-left: 3px solid #4361EE; margin-bottom: 15px;">
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
        
        # Initialize selected agent in session state if not already done
        if "selected_agent" not in st.session_state:
            st.session_state.selected_agent = "Research Expert"
        
        # Define agent descriptions and icons
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
        
        # Add CSS for custom agent selector buttons
        st.markdown("""
        <style>
        /* Custom agent selector styling */
        .agent-selector-container {
            display: flex;
            flex-direction: column;
            gap: 0;
            border-radius: 10px;
            overflow: hidden;
            margin-bottom: 15px;
        }
        
        .agent-selector-title {
            font-weight: 500;
            margin-bottom: 5px !important;
            color: var(--text-primary);
            font-size: 0.9rem;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Create a button for each agent in a single row
        cols = st.columns(len(agent_options))
        
        for i, agent in enumerate(agent_options):
            # Determine if this agent is selected
            is_selected = st.session_state.selected_agent == agent
            
            # Create the button with the appropriate styling
            if cols[i].button(
                f"{agent_icons[agent]} {agent}", 
                key=f"agent_button_{agent.replace(' ', '_')}",
                use_container_width=True,
                type="primary" if is_selected else "secondary"
            ):
                set_agent(agent)
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Get the currently selected agent
        selected_agent = st.session_state.selected_agent
        
        # Display selected agent description
        st.markdown(f"""
        <div style="background-color: #F8FAFC; padding: 10px 15px; border-radius: 8px; border-left: 3px solid #4361EE; margin-bottom: 15px;">
            <p style="margin: 0; font-size: 0.95rem;"><strong>{agent_icons[selected_agent]} {selected_agent}:</strong> {agent_descriptions[selected_agent]}</p>
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
        if prompt := st.chat_input(f"Ask the {selected_agent} a question...", key=f"chat_input_{st.session_state.chat_input_key}"):
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Display user message
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Get response from selected agent
            with st.chat_message("assistant", avatar=agent_icons[selected_agent]):
                with st.spinner(f"Consulting {selected_agent}..."):
                    response = get_agent_response(
                        selected_agent, 
                        prompt, 
                        st.session_state.current_blog_content
                    )
                    st.markdown(response)
            
            # Add assistant response to chat history
            st.session_state.messages.append({
                "role": "assistant", 
                "content": response,
                "avatar": agent_icons[selected_agent]
            })
            
            # Increment the key to create a new input widget on next rerun
            st.session_state.chat_input_key += 1
            st.rerun() 