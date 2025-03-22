from crewai import Agent, Task
from typing import List, Dict, Any
from pydantic import BaseModel
import requests
import streamlit as st
from langchain_community.utilities import GoogleSearchAPIWrapper
import os
from dotenv import load_dotenv
import openai
import json
import hashlib
import time
from pathlib import Path
import traceback  # Import traceback for error reporting

# Import hallucination management system
from app.utils.hallucination_management import HallucinationManagement

# Remove authentication imports
# import streamlit_authenticator as stauth
# import yaml
# from yaml.loader import SafeLoader

# Import our new crew setup
from app.agents.crew_setup import create_blog_crew

# Make sure we load environment variables
load_dotenv()

# Explicitly set OpenAI API key
openai_api_key = os.getenv("OPENAI_API_KEY")
os.environ["OPENAI_API_KEY"] = openai_api_key
openai.api_key = openai_api_key

# Define API base URL
API_BASE_URL = "http://localhost:8000"  # FastAPI default port

# Define cache directory
CACHE_DIR = Path("cache")
CACHE_EXPIRY = 7 * 24 * 60 * 60  # 7 days in seconds

class ResearchTopic(BaseModel):
    """
    Pydantic model for a research topic with validation.
    
    Attributes:
        title: The main topic title
        keywords: List of keywords related to the topic
        depth: The technical depth level (beginner, intermediate, advanced)
    """
    title: str
    keywords: List[str] = []
    depth: str = "intermediate"  # beginner, intermediate, advanced
    
    class Config:
        """Configuration for the Pydantic model."""
        # Example values for documentation
        schema_extra = {
            "example": {
                "title": "Docker Containerization",
                "keywords": ["containers", "virtualization", "microservices"],
                "depth": "intermediate"
            }
        }
    
    @property
    def keyword_count(self) -> int:
        """Return the number of keywords."""
        return len(self.keywords)
    
    def formatted_keywords(self) -> str:
        """Return keywords as a comma-separated string."""
        return ", ".join(self.keywords) if self.keywords else "general overview"
    
    # Validators
    from pydantic import validator
    
    @validator('depth')
    def validate_depth(cls, v):
        """Validate that depth is one of the allowed values."""
        allowed_depths = ["beginner", "intermediate", "advanced"]
        if v not in allowed_depths:
            raise ValueError(f"Depth must be one of: {', '.join(allowed_depths)}")
        return v
    
    @validator('title')
    def validate_title(cls, v):
        """Validate that title is not empty and has reasonable length."""
        if not v or not v.strip():
            raise ValueError("Title cannot be empty")
        if len(v) > 100:
            raise ValueError("Title is too long (max 100 characters)")
        if v.strip().isdigit():
            raise ValueError("Title cannot be numeric only, please provide a descriptive title")
        return v.strip()
    
    @validator('keywords')
    def validate_keywords(cls, v):
        """Validate keywords format."""
        # Ensure all keywords are strings and not empty
        return [k.strip() for k in v if k and k.strip()]

# Define a proper tool function that will be used by the agent
def search_web(query: str) -> str:
    """
    Search the web for information about a topic.
    
    Args:
        query: The search query string
        
    Returns:
        A string containing search results
    """
    try:
        # Initialize the Google Search wrapper
        search = GoogleSearchAPIWrapper()
        
        # Log the search query for debugging
        print(f"Searching for: {query}")
        
        # Execute the search
        results = search.run(query)
        
        # Format and return the results
        return f"Search results for '{query}':\n\n{results}"
    except Exception as e:
        # Handle errors gracefully
        error_msg = f"Error searching the web: {str(e)}"
        print(error_msg)
        return error_msg

def create_researcher_agent() -> Agent:
    """
    Create a research agent with web search capabilities.
    
    Returns:
        A CrewAI Agent configured for technical research
    """
    # Create and return the agent without tools for now
    # We'll use a different approach to incorporate search functionality
    return Agent(
        role='Technical Research Specialist',
        goal='Thoroughly research technical topics and gather accurate, up-to-date information',
        backstory="""You are an experienced technical researcher with a strong background in 
        computer science and software engineering. You excel at finding accurate and relevant 
        information about technical topics. You always verify facts from multiple sources and
        provide comprehensive, well-structured information.""",
        verbose=True,
        allow_delegation=False,
        # Configure the language model
        llm_config={
            "config_list": [{"model": "gpt-4o", "api_key": openai_api_key}],
            "temperature": 0.5,  # More factual responses
            "request_timeout": 120  # Longer timeout for research
        }
    )

def get_cache_key(topic: ResearchTopic) -> str:
    """
    Generate a unique cache key for a research topic.
    
    Args:
        topic: The ResearchTopic object
        
    Returns:
        A string hash that uniquely identifies this research request
    """
    # Create a string representation of the topic
    topic_str = f"{topic.title}_{','.join(sorted(topic.keywords))}_{topic.depth}"
    
    # Generate a hash
    return hashlib.md5(topic_str.encode('utf-8')).hexdigest()

def get_from_cache(cache_key: str) -> Dict[str, Any]:
    """
    Try to retrieve content from cache.
    
    Args:
        cache_key: The unique identifier for the cached content
        
    Returns:
        The cached content or None if not found or expired
    """
    # Ensure cache directory exists
    if not CACHE_DIR.exists():
        CACHE_DIR.mkdir(parents=True)
    
    cache_file = CACHE_DIR / f"{cache_key}.json"
    
    # Check if cache file exists
    if not cache_file.exists():
        return None
    
    try:
        # Read cache file
        with open(cache_file, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
        
        # Check if cache is expired
        if time.time() - cache_data.get('timestamp', 0) > CACHE_EXPIRY:
            print(f"Cache expired for key: {cache_key}")
            return None
        
        print(f"Cache hit for key: {cache_key}")
        return cache_data.get('data')
    
    except Exception as e:
        print(f"Error reading cache: {str(e)}")
        return None

def save_to_cache(cache_key: str, data: Dict[str, Any]) -> None:
    """
    Save content to cache.
    
    Args:
        cache_key: The unique identifier for the content
        data: The data to cache
    """
    # Ensure cache directory exists
    if not CACHE_DIR.exists():
        CACHE_DIR.mkdir(parents=True)
    
    cache_file = CACHE_DIR / f"{cache_key}.json"
    
    try:
        # Prepare cache data with timestamp
        cache_data = {
            'timestamp': time.time(),
            'data': data
        }
        
        # Create a JSON-safe version of the data
        def make_json_safe(obj):
            if isinstance(obj, dict):
                return {k: make_json_safe(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [make_json_safe(item) for item in obj]
            elif isinstance(obj, (str, int, float, bool, type(None))):
                return obj
            else:
                # Convert any other type to string
                return str(obj)
        
        json_safe_data = make_json_safe(cache_data)
        
        # Write to cache file
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(json_safe_data, f, ensure_ascii=False, indent=2)
        
        print(f"Saved to cache: {cache_key}")
    
    except Exception as e:
        print(f"Error saving to cache: {str(e)}")
        import traceback
        traceback.print_exc()  # Print the full stack trace for debugging

def research_topic(topic: ResearchTopic, progress_callback=None, use_cache=True) -> Dict[str, Any]:
    """
    Research a technical topic and return structured information using a multi-agent crew
    
    Args:
        topic: A ResearchTopic object containing title, keywords, and depth
        progress_callback: Optional callback function to report progress
        use_cache: Whether to use cached results if available
        
    Returns:
        A dictionary containing the research results
    """
    # Check if API keys are set
    if not openai_api_key:
        return {"error": "OpenAI API key not set"}
        
    if not (os.getenv("GOOGLE_API_KEY") and os.getenv("GOOGLE_CSE_ID")):
        return {"error": "Google Search API credentials not set"}
    
    try:
        # Check cache first if enabled
        if use_cache:
            cache_key = get_cache_key(topic)
            cached_result = get_from_cache(cache_key)
            
            if cached_result:
                if progress_callback:
                    progress_callback(1.0, "Retrieved from cache")
                print(f"Using cached result for: {topic.title}")
                
                # Add source information to the result
                cached_result["source"] = "cached"
                cached_result["cache_key"] = cache_key
                
                # Get cache timestamp
                try:
                    cache_file = CACHE_DIR / f"{cache_key}.json"
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)
                    cache_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(cache_data.get('timestamp', 0)))
                    cached_result["cached_at"] = cache_time
                except:
                    cached_result["cached_at"] = "unknown time"
                    
                return cached_result
        
        # Create the crew for blog generation
        if progress_callback:
            progress_callback(0.1, "Assembling specialized agent crew...")
            
        crew = create_blog_crew(
            topic_title=topic.title,
            keywords=topic.keywords,
            depth=topic.depth,
            progress_callback=progress_callback
        )
        
        # Run the crew to generate the blog post
        if progress_callback:
            progress_callback(0.4, "Research phase starting...")
            
        # Execute the crew's tasks
        print(f"Starting crew execution for: {topic.title}")
        
        crew_output = crew.kickoff()
        
        # Extract the string content from the CrewOutput object
        # The CrewOutput object is not directly JSON serializable
        if hasattr(crew_output, 'raw_output'):
            result_content = crew_output.raw_output
        elif hasattr(crew_output, 'output'):
            result_content = crew_output.output
        elif hasattr(crew_output, '__str__'):
            result_content = str(crew_output)
        else:
            # If we can't extract the content in a standard way, convert to string
            result_content = str(crew_output)
            
        print(f"Extracted content type: {type(result_content)}")
        
        # Verify content for hallucinations
        if progress_callback:
            progress_callback(0.85, "Verifying content accuracy...")
        
        try:
            # Initialize hallucination management system with GPT-4o
            # Using advanced level for more thorough verification
            hallucination_mgmt = HallucinationManagement(level="advanced", model="gpt-4o")
            
            # Generate search results for factual verification
            search_query = f"{topic.title} {' '.join(topic.keywords)}"
            web_search_results = search_web(search_query)
            
            # Default sources if we don't have specific ones
            sources = []
            
            # Process the content to detect and fix hallucinations
            def verification_callback(message):
                if progress_callback:
                    progress_callback(0.9, f"Verification: {message}")
                    
            verification_result = hallucination_mgmt.process_content(
                query=topic.title,
                content=result_content,
                web_search_results=web_search_results,
                sources=sources,
                callback=verification_callback
            )
            
            # Use the verified content
            verified_content = verification_result["processed_content"]
            hallucination_metrics = verification_result["hallucination_metrics"]
            
            # Check if we need an additional verification pass for higher quality
            final_score = hallucination_metrics['summary']['final_score']
            if final_score < 0.9 and progress_callback:
                progress_callback(0.92, "Performing additional verification...")
                
                # Try another round of verification with the already improved content
                second_verification = hallucination_mgmt.process_content(
                    query=topic.title,
                    content=verified_content,  # Use the already improved content
                    web_search_results=web_search_results,
                    sources=sources,
                    callback=verification_callback
                )
                
                # If the second verification improved the score, use its results
                if second_verification["hallucination_metrics"]["summary"]["final_score"] > final_score:
                    verified_content = second_verification["processed_content"]
                    hallucination_metrics = second_verification["hallucination_metrics"]
            
            # Log verification metrics
            print(f"Content verification completed: Initial score: {hallucination_metrics['summary']['initial_score']:.2f}, Final score: {hallucination_metrics['summary']['final_score']:.2f}")
            
            # Use the verified content as our final content
            result_content = verified_content
            
        except Exception as verif_error:
            # If verification fails, log the error but continue with original content
            print(f"Warning: Content verification failed: {str(verif_error)}")
            traceback.print_exc()
            hallucination_metrics = None
        
        # This may not be reached due to the callbacks in crew_setup.py,
        # but we include it as a fallback
        if progress_callback:
            progress_callback(0.98, "Finalizing blog post...")
        
        print(f"Crew execution completed for: {topic.title}")
        
        # Structure the results
        result = {
            "title": topic.title,
            "content": result_content,
            "depth": topic.depth,
            "keywords": topic.keywords,
            "source": "freshly_generated",
            "generated_at": time.strftime('%Y-%m-%d %H:%M:%S'),
            "metadata": {
                "topic": topic.title,
                "depth": topic.depth,
                "keywords": topic.keywords
            }
        }
        
        # Add hallucination metrics if available
        if 'hallucination_metrics' in locals() and hallucination_metrics:
            result['hallucination_metrics'] = hallucination_metrics
        
        # Save to cache if enabled
        if use_cache:
            try:
                cache_key = get_cache_key(topic)
                save_to_cache(cache_key, result)
            except Exception as cache_error:
                print(f"Warning: Failed to save to cache: {str(cache_error)}")
                # Continue execution even if caching fails
            
        if progress_callback:
            progress_callback(1.0, "Done!")
            
        return result
    except Exception as e:
        # Handle and log any errors
        error_message = f"Research failed: {str(e)}"
        print(error_message)
        import traceback
        traceback.print_exc()  # Print the full stack trace for debugging
        if progress_callback:
            progress_callback(0, f"Error: {error_message}")
        return {"error": error_message} 

# Simulate authenticated state for sidebar use in the app
name = "Administrator"
authentication_status = True
username = "admin" 