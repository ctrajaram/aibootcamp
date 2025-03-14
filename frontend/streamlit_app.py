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
from app.auth import require_auth
# Import ResearchTopic from researcher module
from app.agents.researcher import ResearchTopic, research_topic

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
    /* Material UI inspired styling */
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');
    
    * {
        font-family: 'Roboto', sans-serif;
    }
    
    .main-header {
        font-size: 2.8rem;
        color: #1976D2;
        font-weight: 700;
        margin-bottom: 1.5rem;
        text-align: center;
        padding: 1rem;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
    }
    
    .sub-header {
        font-size: 1.5rem;
        color: #0D47A1;
        font-weight: 500;
        margin-top: 2rem;
        border-bottom: 2px solid #E3F2FD;
        padding-bottom: 0.5rem;
    }
    
    .description {
        color: #424242;
        font-size: 1.1rem;
        margin: 0 auto 0.5rem auto;
        background-color: transparent;
        padding: 0.8rem;
        border-radius: 0;
        box-shadow: none;
        max-width: 90%;
        text-align: center;
        line-height: 1.6;
    }
    
    .success-box {
        background-color: #E8F5E9;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border-left: 5px solid #4CAF50;
    }
    
    .info-box {
        background-color: #E3F2FD;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border-left: 5px solid #2196F3;
    }
    
    /* Material UI inspired buttons */
    .stButton button {
        background-color: #1976D2;
        color: white;
        font-weight: 500;
        border-radius: 4px;
        padding: 0.6rem 1.2rem;
        border: none;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        transition: all 0.3s ease;
    }
    
    .stButton button:hover {
        background-color: #1565C0;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        transform: translateY(-2px);
    }
    
    .stButton button:active {
        transform: translateY(0);
        box-shadow: 0 2px 3px rgba(0,0,0,0.2);
    }
    
    .stDownloadButton button {
        background-color: #43A047;
        color: white;
        font-weight: 500;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }
    
    .stDownloadButton button:hover {
        background-color: #388E3C;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        transform: translateY(-2px);
    }
    
    /* Material UI inspired inputs */
    .stTextInput input, .stTextArea textarea {
        border-radius: 4px;
        border: 1px solid #BDBDBD;
        padding: 0.7rem;
        transition: all 0.3s ease;
        background-color: transparent;
    }
    
    .stTextInput input:focus, .stTextArea textarea:focus {
        border: 1px solid #1976D2;
        box-shadow: 0 0 0 2px rgba(25,118,210,0.2);
    }
    
    /* Material UI inspired slider */
    .stSlider div[data-baseweb="slider"] {
        margin-top: 1rem;
    }
    
    /* Divider styling */
    hr {
        margin: 1rem 0;
        border: none;
        height: 1px;
        background-color: #E0E0E0;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        font-weight: 500;
        color: #1976D2;
    }
    
    /* Center content */
    .center-content {
        display: flex;
        justify-content: center;
        align-items: center;
        flex-direction: column;
    }
    
    /* Card-like containers */
    .card-container {
        background-color: white;
        border-radius: 8px;
        padding: 1.5rem;
        box-shadow: 0 3px 10px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
    }
    
    .cache-box {
        background-color: #f0f8ff;
        border-left: 5px solid #1e90ff;
        padding: 10px;
        margin-bottom: 20px;
        border-radius: 5px;
        font-weight: bold;
        color: #1e90ff;
    }
    
    .cache-details {
        margin-top: 5px;
        color: #666;
        font-weight: normal;
    }
    
    /* Blog preview styling */
    .blog-preview {
        font-family: 'Roboto', sans-serif;
        line-height: 1.6;
        padding: 20px;
        background-color: #fff;
        border-radius: 8px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    
    .blog-preview h1, 
    .blog-preview h2, 
    .blog-preview h3, 
    .blog-preview h4, 
    .blog-preview h5, 
    .blog-preview h6 {
        color: #1976D2;
        margin-top: 1.5em;
        margin-bottom: 0.8em;
        font-weight: 500;
    }
    
    .blog-preview h1 {
        font-size: 2em;
        border-bottom: 2px solid #E3F2FD;
        padding-bottom: 0.3em;
    }
    
    .blog-preview h2 {
        font-size: 1.5em;
        border-bottom: 1px solid #E3F2FD;
        padding-bottom: 0.2em;
    }
    
    .blog-preview h3 {
        font-size: 1.3em;
    }
    
    .blog-preview p {
        margin-bottom: 1em;
        color: #333;
    }
    
    .blog-preview code {
        background-color: #f5f7f9;
        border-radius: 3px;
        font-family: monospace;
        padding: 0.2em 0.4em;
        font-size: 0.9em;
    }
    
    .blog-preview pre {
        background-color: #f5f7f9;
        border-radius: 5px;
        padding: 1em;
        overflow-x: auto;
        margin: 1em 0;
    }
    
    .blog-preview pre code {
        background-color: transparent;
        padding: 0;
    }
    
    .blog-preview blockquote {
        border-left: 4px solid #1976D2;
        padding-left: 1em;
        margin-left: 0;
        color: #555;
        font-style: italic;
    }
    
    /* Phase indicator */
    .phase-indicator {
        text-align: center;
        font-weight: bold;
        margin: 15px 0;
        padding: 10px;
        border-radius: 5px;
        background-color: #f5f5f5;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        animation: fadeIn 0.5s ease-in-out;
    }
    
    /* Main UI frame */
    .main-ui-frame {
        border-radius: 16px;
        padding: 2px;
        margin: 20px auto;
        max-width: 95%;
        background: linear-gradient(135deg, #6e8efb, #a777e3);
        box-shadow: 0 8px 20px rgba(0,0,0,0.12);
    }
    
    .main-ui-content {
        background-color: white;
        border-radius: 14px;
        padding: 25px;
        height: 100%;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
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
st.markdown('<div class="main-header">✨ Technical Blog Generator ✨</div>', unsafe_allow_html=True)
st.markdown('<div class="description">Generate comprehensive technical blog posts with AI assistance. This tool helps you create accurate, well-researched technical content with just a few clicks.</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# Add a small space after the description
st.markdown('<div style="margin-bottom: 0.5rem;"></div>', unsafe_allow_html=True)

# Add a dark mode toggle in the sidebar
with st.sidebar:
    st.title("Settings")
    dark_mode = st.toggle("Dark Mode", value=False)
    compact_view = st.toggle("Compact View", value=False)
    
    if dark_mode:
        # Apply dark mode styling
        st.markdown("""
        <style>
            body {
                background-color: #121212;
                color: #f0f0f0;
            }
            .main-header {
                color: #90CAF9;
            }
            .description {
                background-color: transparent;
                color: #e0e0e0;
            }
            .card-container {
                background-color: #1E1E1E;
                box-shadow: 0 3px 10px rgba(0,0,0,0.4);
            }
            .agent-card {
                background-color: #2D2D2D;
                color: #e0e0e0;
            }
            .stTextInput input, .stTextArea textarea {
                background-color: #2D2D2D;
                color: #e0e0e0;
                border-color: #555;
            }
            .stTextInput input:focus, .stTextArea textarea:focus {
                border-color: #90CAF9;
            }
            .streamlit-expanderHeader {
                color: #90CAF9;
            }
            .stTabs [data-baseweb="tab-list"] {
                background-color: #1E1E1E;
            }
            .stTabs [data-baseweb="tab"] {
                color: #e0e0e0;
            }
            .stTabs [aria-selected="true"] {
                background-color: #2D2D2D;
                color: #90CAF9;
            }
            /* Dark mode for blog preview */
            .blog-preview {
                background-color: #1E1E1E;
                color: #e0e0e0;
                box-shadow: 0 2px 5px rgba(0,0,0,0.4);
            }
            .blog-preview h1, 
            .blog-preview h2, 
            .blog-preview h3, 
            .blog-preview h4, 
            .blog-preview h5, 
            .blog-preview h6 {
                color: #90CAF9;
            }
            .blog-preview h1,
            .blog-preview h2 {
                border-bottom-color: #333;
            }
            .blog-preview p {
                color: #e0e0e0;
            }
            .blog-preview code {
                background-color: #2D2D2D;
                color: #e0e0e0;
            }
            .blog-preview pre {
                background-color: #2D2D2D;
            }
            .blog-preview blockquote {
                border-left-color: #90CAF9;
                color: #bbb;
            }
        </style>
        """, unsafe_allow_html=True)
    
    if compact_view:
        # Apply compact view styling
        st.markdown("""
        <style>
            .main-header {
                font-size: 2rem;
                margin-bottom: 0.8rem;
                padding: 0.5rem;
            }
            .description {
                font-size: 0.9rem;
                padding: 0.8rem;
                margin-bottom: 1rem;
            }
            .card-container {
                padding: 1rem;
                margin: 0.5rem 0;
            }
            .stButton button {
                padding: 0.4rem 0.8rem;
            }
            .agent-card {
                padding: 8px;
            }
            .agent-icon {
                font-size: 20px;
                margin-bottom: 4px;
            }
            .agent-name {
                font-size: 0.8rem;
                margin-bottom: 4px;
            }
            .agent-description {
                font-size: 0.7rem;
                height: 30px;
            }
            div.row-widget.stRadio > div {
                flex-direction: row;
                align-items: center;
            }
            div.row-widget.stRadio > div > label {
                padding: 0.2rem 0.5rem;
                margin: 0 0.2rem;
            }
            .stTabs [data-baseweb="tab"] {
                padding-top: 0.4rem;
                padding-bottom: 0.4rem;
            }
            .streamlit-expanderHeader {
                font-size: 0.9rem;
                padding: 0.4rem;
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
    # Depth selector with better styling
    st.markdown("### 📊 Content Depth")
    depth = st.select_slider(
        "",
        options=["beginner", "intermediate", "advanced"],
        value="intermediate"
    )

with col2:
    # Add cache control
    st.markdown("### 🔄 Cache Control")
    use_cache = st.checkbox("Use cached results if available", value=True,
                           help="Faster results, but may not include the latest information")
    if not use_cache:
        st.caption("⚠️ Generating fresh content uses more API credits")

# Removing the closing card container div
# st.markdown('</div>', unsafe_allow_html=True)

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