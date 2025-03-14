import streamlit as st

# Configure the app - MUST be the first Streamlit command
st.set_page_config(
    page_title="Technical Blog Generator",
    page_icon="📝",
    layout="wide"
)

import requests
from typing import List
import json
import sys
import os
from dotenv import load_dotenv

# Add the app directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.agents.researcher import ResearchTopic, research_topic

# Load environment variables
load_dotenv()

# Define API base URL
API_BASE_URL = "http://localhost:8000"  # FastAPI default port

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
        margin: 0 auto 2rem auto;
        background-color: #F5F7F9;
        padding: 1.2rem;
        border-radius: 8px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
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
        margin: 2rem 0;
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
        margin: 1rem 0;
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
st.markdown('<div class="center-content">', unsafe_allow_html=True)
st.markdown('<div class="main-header">✨ Technical Blog Generator ✨</div>', unsafe_allow_html=True)
st.markdown('<div class="description">Generate comprehensive technical blog posts with AI assistance. This tool helps you create accurate, well-researched technical content with just a few clicks.</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# Input section in a card-like container
st.markdown('<div class="card-container">', unsafe_allow_html=True)
# Create columns for a more organized layout
col1, col2 = st.columns(2)

with col1:
    topic = st.text_input("📌 Enter your technical topic:", placeholder="e.g., Docker containerization")

with col2:
    keywords = st.text_input("🔑 Enter keywords (comma-separated):", placeholder="e.g., containers, virtualization, microservices")

# Depth selector with better styling
st.markdown("### 📊 Content Depth")
depth = st.select_slider(
    "",
    options=["beginner", "intermediate", "advanced"],
    value="intermediate"
)
st.markdown('</div>', unsafe_allow_html=True)

# Add a divider
st.markdown("<hr>", unsafe_allow_html=True)

# Create a single button and store its state - centered
st.markdown('<div class="center-content">', unsafe_allow_html=True)
generate_clicked = st.button("🚀 Generate Content", key="generate_content_button")
st.markdown('</div>', unsafe_allow_html=True)

if generate_clicked:
    if topic:
        with st.spinner("🔍 Researching and generating content..."):
            try:
                # Convert inputs to ResearchTopic
                research_request = ResearchTopic(
                    title=topic,
                    keywords=[k.strip() for k in keywords.split(",") if k.strip()],
                    depth=depth
                )
                
                # Use the researcher directly instead of making API calls
                result = research_topic(research_request)
                
                # Check for errors
                if "error" in result:
                    st.error(f"Error: {result['error']}")
                    if "OpenAI API key not set" in result["error"]:
                        st.info("Please add your OpenAI API key to the .env file in your project root")
                    st.stop()
                
                # Display results in a card container
                st.markdown('<div class="card-container">', unsafe_allow_html=True)
                
                # Success message
                st.markdown('<div class="success-box">✅ Content generated successfully!</div>', unsafe_allow_html=True)
                
                # Add composer/editor area
                st.markdown('<div class="sub-header">Generated Blog Post</div>', unsafe_allow_html=True)
                
                # Add a preview of the content in a nice box
                st.markdown('<div class="info-box">📄 Preview</div>', unsafe_allow_html=True)
                st.markdown(result["content"][:500] + "...")
                
                # Create a text area for editing the generated content
                generated_content = result["content"]
                edited_content = st.text_area(
                    "✏️ Edit your blog post",
                    value=generated_content,
                    height=400,
                    key="blog_editor"
                )
                
                # Center the download button
                st.markdown('<div class="center-content">', unsafe_allow_html=True)
                # Replace the two-button approach with a direct download button
                st.download_button(
                    label="📥 Download Blog Post as Markdown",
                    data=edited_content,
                    file_name=f"{topic.lower().replace(' ', '_')}_blog.md",
                    mime="text/markdown",
                    key="download_button",
                    help="Click to download your blog post as a Markdown file"
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
                
            except Exception as e:
                st.error(f"Error generating content: {str(e)}")
                st.info("If this is an API key error, please check that your OpenAI API key is valid and has sufficient credits")
    else:
        st.error("Please provide a topic") 