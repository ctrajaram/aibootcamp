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
    st.session_state.compact_view = False

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
    /* Modern UI styling with improved aesthetics */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    /* Modern main header */
    .main-header {
        font-size: 2.5rem;
        color: #4361EE;
        font-weight: 700;
        margin-bottom: 1.2rem;
        text-align: center;
        padding: 1rem;
        text-shadow: 0px 2px 4px rgba(0,0,0,0.1);
        letter-spacing: -0.5px;
    }
    
    /* Modern sub-header */
    .sub-header {
        font-size: 1.5rem;
        color: #3A0CA3;
        font-weight: 600;
        margin-top: 1.8rem;
        border-bottom: 2px solid #F1F5F9;
        padding-bottom: 0.5rem;
        letter-spacing: -0.3px;
    }
    
    /* Modern description */
    .description {
        color: #4B5563;
        font-size: 1.1rem;
        margin: 0 auto 0.5rem auto;
        background-color: transparent;
        padding: 0.8rem;
        border-radius: 0;
        box-shadow: none;
        max-width: 90%;
        text-align: center;
        line-height: 1.6;
        font-weight: 400;
    }
    
    /* Modern success box */
    .success-box {
        background-color: #ECFDF5;
        padding: 1rem;
        border-radius: 12px;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border-left: 5px solid #10B981;
    }
    
    /* Modern info box */
    .info-box {
        background-color: #EFF6FF;
        padding: 1rem;
        border-radius: 12px;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border-left: 5px solid #3B82F6;
    }
    
    /* Modern buttons */
    .stButton button {
        background-color: #4361EE;
        color: white;
        font-weight: 600;
        border-radius: 8px;
        padding: 0.7rem 1.4rem;
        border: none;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        box-shadow: 0 4px 6px rgba(67, 97, 238, 0.25);
        transition: all 0.3s ease;
    }
    
    .stButton button:hover {
        background-color: #3A56D4;
        box-shadow: 0 6px 10px rgba(67, 97, 238, 0.3);
        transform: translateY(-2px);
    }
    
    .stButton button:active {
        transform: translateY(0);
        box-shadow: 0 2px 3px rgba(67, 97, 238, 0.2);
    }
    
    /* Modern download button */
    .stDownloadButton button {
        background-color: #10B981;
        color: white;
        font-weight: 600;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(16, 185, 129, 0.25);
    }
    
    .stDownloadButton button:hover {
        background-color: #059669;
        box-shadow: 0 6px 10px rgba(16, 185, 129, 0.3);
        transform: translateY(-2px);
    }
    
    /* Modern inputs */
    .stTextInput input, .stTextArea textarea {
        border-radius: 8px;
        border: 1px solid #E5E7EB;
        padding: 0.8rem;
        transition: all 0.3s ease;
        background-color: #F9FAFB;
        font-size: 1rem;
    }
    
    .stTextInput input:focus, .stTextArea textarea:focus {
        border: 1px solid #4361EE;
        box-shadow: 0 0 0 3px rgba(67, 97, 238, 0.15);
        background-color: white;
    }
    
    /* Modern slider */
    .stSlider div[data-baseweb="slider"] {
        margin-top: 1rem;
    }
    
    .stSlider [data-testid="stThumbValue"] {
        background-color: #4361EE !important;
        color: white !important;
        font-weight: 600 !important;
        padding: 2px 8px !important;
        border-radius: 6px !important;
    }
    
    /* Modern divider */
    hr {
        margin: 1.5rem 0;
        border: none;
        height: 1px;
        background-color: #E5E7EB;
    }
    
    /* Modern expander */
    .streamlit-expanderHeader {
        font-weight: 600;
        color: #4361EE;
        background-color: #F8FAFC;
        border-radius: 8px;
        padding: 0.5rem 1rem !important;
    }
    
    /* Center content */
    .center-content {
        display: flex;
        justify-content: center;
        align-items: center;
        flex-direction: column;
    }
    
    /* Modern card containers */
    .card-container {
        background-color: white;
        border-radius: 12px;
        padding: 1.8rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        margin: 1rem 0;
        border: 1px solid #F1F5F9;
    }
    
    /* Modern cache box */
    .cache-box {
        background-color: #EFF6FF;
        border-left: 5px solid #3B82F6;
        padding: 12px;
        margin-bottom: 20px;
        border-radius: 8px;
        font-weight: 600;
        color: #2563EB;
    }
    
    .cache-details {
        margin-top: 5px;
        color: #6B7280;
        font-weight: normal;
    }
    
    /* Modern section headers */
    [data-testid="stMarkdownContainer"] h3 {
        color: #4361EE;
        font-weight: 600;
        font-size: 1.25rem;
        margin-bottom: 0.75rem;
        display: flex;
        align-items: center;
        letter-spacing: -0.3px;
    }
    
    /* Modern tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #F8FAFC;
        padding: 8px;
        border-radius: 12px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 8px 16px;
        font-weight: 500;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #4361EE !important;
        color: white !important;
    }
    
    /* Modern chat interface */
    [data-testid="stChatMessage"] {
        background-color: #F8FAFC;
        border-radius: 12px;
        padding: 12px;
        margin-bottom: 12px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    
    [data-testid="stChatMessageContent"] {
        color: #1F2937;
    }
    
    /* Modern selectbox */
    [data-baseweb="select"] {
        border-radius: 8px;
    }
    
    [data-baseweb="select"] > div {
        background-color: #F9FAFB;
        border-color: #E5E7EB;
        border-radius: 8px;
    }
    
    /* Modern checkbox */
    [data-testid="stCheckbox"] > div > div {
        background-color: #4361EE;
        border-radius: 4px;
    }
    
    /* Clear chat history button */
    button[kind="secondary"] {
        background-color: #6B7280;
        color: white;
        font-weight: 600;
        border-radius: 8px;
    }
    
    button[kind="secondary"]:hover {
        background-color: #4B5563;
    }
    
    /* Modern caption text */
    .stCaption {
        color: #6B7280;
        font-size: 0.9rem;
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
            border-bottom: 1px solid #e0e0e0;
        }
        
        /* Style the logout button specifically */
        .logout-section {
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 1px solid #e0e0e0;
        }
        </style>
        <div class="logout-button">
        </div>
        """, unsafe_allow_html=True)
        
        # Display user info and logout button
        st.markdown(f"**Logged in as:** {name}")
        
        # Create a dedicated logout button with a unique key
        if st.button("Sign Out", key="sidebar_logout_button"):
            # Call the logout function
            logout()
            # Clear all session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            # Force a rerun to redirect to login page
            st.rerun()
    
    # Use session state to track button clicks without direct rerun in callbacks
    if "dark_mode_clicked" not in st.session_state:
        st.session_state.dark_mode_clicked = False
    if "compact_view_clicked" not in st.session_state:
        st.session_state.compact_view_clicked = False
    
    # Define callback functions that only update state variables
    def toggle_dark_mode():
        st.session_state.dark_mode_clicked = True
        
    def toggle_compact_view():
        st.session_state.compact_view_clicked = True
    
    # Create buttons instead of toggles for more reliable behavior
    dark_mode_label = "🌙 Disable Dark Mode" if st.session_state.dark_mode else "🌙 Enable Dark Mode"
    compact_view_label = "📏 Disable Compact View" if st.session_state.compact_view else "📏 Enable Compact View"
    
    st.button(dark_mode_label, on_click=toggle_dark_mode, key="dark_mode_button")
    st.button(compact_view_label, on_click=toggle_compact_view, key="compact_view_button")
    
    # Handle the actual toggling outside of callbacks
    if st.session_state.dark_mode_clicked:
        st.session_state.dark_mode = not st.session_state.dark_mode
        st.session_state.dark_mode_clicked = False
        st.rerun()
        
    if st.session_state.compact_view_clicked:
        st.session_state.compact_view = not st.session_state.compact_view
        st.session_state.compact_view_clicked = False
        st.rerun()
    
    # Display current theme status
    st.caption(f"Current theme: {'Dark' if st.session_state.dark_mode else 'Light'}, {'Compact' if st.session_state.compact_view else 'Standard'}")
    
    # Apply dark mode styling if enabled
    if st.session_state.dark_mode:
        st.markdown("""
        <style>
            .stApp {
                background-color: #121212;
                color: #f0f0f0;
            }
            .main-header {
                color: #90CAF9 !important;
            }
            .description {
                background-color: transparent !important;
                color: #e0e0e0 !important;
            }
            .card-container {
                background-color: #1E1E1E !important;
                box-shadow: 0 3px 10px rgba(0,0,0,0.4) !important;
            }
            .stTextInput input, .stTextArea textarea {
                background-color: #2D2D2D !important;
                color: #e0e0e0 !important;
                border-color: #555 !important;
            }
            .stTextInput input:focus, .stTextArea textarea:focus {
                border-color: #90CAF9 !important;
            }
            .streamlit-expanderHeader {
                color: #90CAF9 !important;
            }
            /* Dark mode for blog preview */
            .blog-preview {
                background-color: #1E1E1E !important;
                color: #e0e0e0 !important;
            }
            .blog-preview h1, 
            .blog-preview h2, 
            .blog-preview h3, 
            .blog-preview h4, 
            .blog-preview h5, 
            .blog-preview h6 {
                color: #90CAF9 !important;
            }
            .blog-preview p {
                color: #e0e0e0 !important;
            }
            .blog-preview code {
                background-color: #2D2D2D !important;
                color: #e0e0e0 !important;
            }
            .blog-preview pre {
                background-color: #2D2D2D !important;
            }
            .stMarkdown {
                color: #e0e0e0 !important;
            }
            .stButton button {
                border: 1px solid #555 !important;
            }
            .stTabs [data-baseweb="tab-list"] {
                background-color: #1E1E1E !important;
            }
            .stTabs [data-baseweb="tab"] {
                color: #e0e0e0 !important;
            }
            .stTabs [aria-selected="true"] {
                background-color: #2D2D2D !important;
                color: #90CAF9 !important;
            }
            .stSelectbox [data-baseweb="select"] {
                background-color: #2D2D2D !important;
            }
            .stSelectbox [data-baseweb="select"] > div {
                background-color: #2D2D2D !important;
                color: #e0e0e0 !important;
            }
        </style>
        """, unsafe_allow_html=True)
    
    # Apply compact view styling if enabled
    if st.session_state.compact_view:
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

# Add project roadmap in sidebar
with st.sidebar:
    st.markdown("---")
    st.markdown("### 🗺️ Project Roadmap")
    
    # Current Features
    st.markdown("""
    #### ✅ Implemented Features
    
    **🎯 Core Features**
    - AI Blog Generation
    - Multi-Expert Chat System
    - Content Caching
    - Markdown/HTML Export
    
    **🔐 Security**
    - Basic Authentication
    - Session Management
    - API Key Protection
    
    **💅 UI/UX**
    - Dark/Light Mode
    - Compact View
    - Modern Design
    - Responsive Layout
    
    **🤖 AI Experts**
    - Research Expert (🔍)
    - Content Editor (✏️)
    - Technical Reviewer (🛠️)
    - SEO Specialist (📈)
    """)
    
    # Progress Indicators
    st.markdown("#### 🚀 Development Progress")
    
    # Calculate progress for each area
    core_progress = 85
    security_progress = 60
    ux_progress = 75
    ai_progress = 70
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("Core")
        st.progress(core_progress/100)
        
        st.markdown("Security")
        st.progress(security_progress/100)
    
    with col2:
        st.markdown("UX/UI")
        st.progress(ux_progress/100)
        
        st.markdown("AI Features")
        st.progress(ai_progress/100)
    
    # Upcoming Features
    st.markdown("""
    #### 🔮 Coming Soon
    
    **📱 Enhanced UX**
    - Auto-save functionality
    - Advanced loading states
    - Progress tracking
    - Keyboard shortcuts
    
    **🤝 Agent Improvements**
    - Agent collaboration
    - Direct content editing
    - Chat history persistence
    - Custom agent creation
    
    **🔒 Advanced Security**
    - User registration
    - OAuth integration
    - Role-based access
    
    **📊 Analytics**
    - Content metrics
    - Usage statistics
    - Performance tracking
    
    **💾 Data Management**
    - Blog versioning
    - Export templates
    - Bulk operations
    """)
    
    # Deployment Status
    st.markdown("""
    #### 🌐 Deployment
    - Local Development ✅
    - AWS Setup 🔄
    - Security Hardening 🔄
    - Performance Optimization 🔄
    """)
    
    st.markdown("---")

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
main_tab, chat_tab = st.tabs(["📝 Blog Generator", "💬 Chat with Research Expert"])

with main_tab:
    # Add a divider
    st.markdown("<hr>", unsafe_allow_html=True)

    # Create a single button and store its state - centered
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