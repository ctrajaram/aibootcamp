from crewai import Agent, Task
from typing import List
from pydantic import BaseModel
import requests
import streamlit as st
from langchain_community.utilities import GoogleSearchAPIWrapper
import os
from dotenv import load_dotenv
import openai

# Make sure we load environment variables
load_dotenv()

# Explicitly set OpenAI API key
openai_api_key = os.getenv("OPENAI_API_KEY")
os.environ["OPENAI_API_KEY"] = openai_api_key
openai.api_key = openai_api_key

# Define API base URL
API_BASE_URL = "http://localhost:8000"  # FastAPI default port

class ResearchTopic(BaseModel):
    title: str
    keywords: List[str]
    depth: str = "intermediate"  # beginner, intermediate, advanced

def search_web(query: str) -> str:
    """Search the web for information"""
    search = GoogleSearchAPIWrapper()
    return search.run(query)

def create_researcher_agent() -> Agent:
    return Agent(
        role='Technical Research Specialist',
        goal='Thoroughly research technical topics and gather accurate, up-to-date information',
        backstory="""You are an experienced technical researcher with a strong background in 
        computer science and software engineering. You excel at finding accurate and relevant 
        information about technical topics.""",
        verbose=True,
        allow_delegation=False,
        # Explicitly pass API key to agent
        llm_config={"api_key": openai_api_key}
    )

def research_topic(topic: ResearchTopic) -> dict:
    """
    Research a technical topic and return structured information
    """
    # Check if API keys are set
    if not openai_api_key:
        return {"error": "OpenAI API key not set"}
        
    if not (os.getenv("GOOGLE_API_KEY") and os.getenv("GOOGLE_CSE_ID")):
        return {"error": "Google Search API credentials not set"}
    
    # Create the researcher agent
    researcher = create_researcher_agent()
    
    # Create a proper Task object with expected_output
    research_task = Task(
        description=f"""Research the topic: {topic.title}
        Keywords to focus on: {', '.join(topic.keywords)}
        Required depth: {topic.depth}
        
        First, search the web for recent information about this topic.
        
        Then provide:
        1. A comprehensive summary
        2. Key technical points
        3. Code examples if applicable
        4. References to authoritative sources
        
        Format the response as a complete blog post with markdown formatting.
        """,
        expected_output="A comprehensive technical blog post with accurate information, code examples, and references.",
        agent=researcher
    )
    
    try:
        # Execute the task
        research_result = researcher.execute_task(research_task)
        
        # Structure the results
        return {
            "title": topic.title,
            "content": research_result,
            "depth": topic.depth,
            "keywords": topic.keywords
        }
    except Exception as e:
        return {"error": f"Research failed: {str(e)}"} 