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

# Make sure we load environment variables
load_dotenv()

# Explicitly set OpenAI API key
openai_api_key = os.getenv("OPENAI_API_KEY")
os.environ["OPENAI_API_KEY"] = openai_api_key
openai.api_key = openai_api_key

# Define API base URL
API_BASE_URL = "http://localhost:8000"  # FastAPI default port

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
            "config_list": [{"model": "gpt-4", "api_key": openai_api_key}],
            "temperature": 0.5,  # More factual responses
            "request_timeout": 120  # Longer timeout for research
        }
    )

def research_topic(topic: ResearchTopic, progress_callback=None) -> Dict[str, Any]:
    """
    Research a technical topic and return structured information
    
    Args:
        topic: A ResearchTopic object containing title, keywords, and depth
        progress_callback: Optional callback function to report progress
        
    Returns:
        A dictionary containing the research results
    """
    # Check if API keys are set
    if not openai_api_key:
        return {"error": "OpenAI API key not set"}
        
    if not (os.getenv("GOOGLE_API_KEY") and os.getenv("GOOGLE_CSE_ID")):
        return {"error": "Google Search API credentials not set"}
    
    try:
        # Create the researcher agent
        researcher = create_researcher_agent()
        
        # Prepare keywords string
        keywords_str = ', '.join(topic.keywords) if topic.keywords else "general overview"
        
        # Perform initial web searches to gather information
        search_results = []
        search_queries = [
            f"{topic.title} overview",
            f"{topic.title} {keywords_str}",
            f"{topic.title} tutorial {topic.depth} level",
            f"{topic.title} best practices 2023",
            f"{topic.title} code examples"
        ]
        
        print("Performing initial web searches...")
        if progress_callback:
            progress_callback(0, "Starting web searches...")
            
        total_queries = len(search_queries)
        for i, query in enumerate(search_queries):
            if progress_callback:
                progress_callback(i / total_queries * 0.5, f"Searching: {query}")
                
            result = search_web(query)
            search_results.append(f"Query: {query}\n{result}\n")
            
            if progress_callback:
                progress_callback((i + 1) / total_queries * 0.5, f"Completed search {i+1}/{total_queries}")
        
        combined_search_results = "\n".join(search_results)
        print(f"Completed {len(search_queries)} web searches")
        
        if progress_callback:
            progress_callback(0.5, "Web searches complete. Starting content generation...")
        
        # Create a proper Task object with detailed instructions and search results
        research_task = Task(
            description=f"""Research the technical topic: "{topic.title}" thoroughly.
            
            Focus on these keywords: {keywords_str}
            Technical depth level: {topic.depth}
            
            I've already performed some web searches for you. Here are the results:
            
            {combined_search_results}
            
            Based on this information and your knowledge, create a comprehensive technical blog post that includes:
            1. A clear introduction to the topic
            2. Key concepts and technical details (appropriate for {topic.depth} level)
            3. Current best practices and methodologies
            4. Code examples where relevant
            5. Comparison of different approaches or technologies
            6. Recent developments or trends
            7. Practical applications
            8. References to authoritative sources
            
            Format your response as a complete, well-structured technical blog post using Markdown.
            Include proper headings, code blocks, and formatting.
            """,
            expected_output="A comprehensive technical blog post with accurate information, code examples, and references, formatted in Markdown.",
            agent=researcher
        )
        
        # Execute the task and get the research result
        print(f"Starting research analysis on: {topic.title}")
        if progress_callback:
            progress_callback(0.6, "Analyzing search results and generating content...")
            
        research_result = researcher.execute_task(research_task)
        
        print(f"Research completed for: {topic.title}")
        if progress_callback:
            progress_callback(1.0, "Content generation complete!")
        
        # Structure and return the results
        return {
            "title": topic.title,
            "content": research_result,
            "depth": topic.depth,
            "keywords": topic.keywords
        }
    except Exception as e:
        # Handle and log any errors
        error_message = f"Research failed: {str(e)}"
        print(error_message)
        if progress_callback:
            progress_callback(0, f"Error: {error_message}")
        return {"error": error_message} 