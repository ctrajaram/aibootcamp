from crewai import Agent, Task, Crew
from typing import List
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from langchain.tools import Tool
from langchain_community.utilities import GoogleSearchAPIWrapper

# Load environment variables
load_dotenv()

# Get API keys
openai_api_key = os.getenv("OPENAI_API_KEY")
os.environ["OPENAI_API_KEY"] = openai_api_key

class BlogRequest(BaseModel):
    topic: str
    keywords: List[str]
    depth: str = "intermediate"

def search_web(query: str) -> str:
    """Search the web for information about technical topics"""
    try:
        search = GoogleSearchAPIWrapper()
        results = search.run(query)
        return results
    except Exception as e:
        return f"Error searching the web: {str(e)}"

def create_blog_crew(request: BlogRequest):
    # Create search tool
    search_tool = Tool(
        name="web_search",
        func=search_web,
        description="Search the internet for information about technical topics"
    )
    
    # Create specialized agents
    researcher = Agent(
        role='Technical Research Specialist',
        goal='Research the technical topic thoroughly and gather accurate information',
        backstory="""You are an experienced technical researcher with expertise in finding
        accurate and relevant information about complex technical topics.""",
        tools=[search_tool],
        verbose=True
    )
    
    writer = Agent(
        role='Technical Content Writer',
        goal='Write engaging, accurate technical content based on research',
        backstory="""You are a skilled technical writer who can explain complex concepts
        clearly and create engaging blog posts that are technically accurate.""",
        verbose=True
    )
    
    # Create tasks for each agent
    research_task = Task(
        description=f"""Research the topic: {request.topic}
        Keywords to focus on: {', '.join(request.keywords)}
        Required depth: {request.depth}
        
        Use the web_search tool to find the most relevant and up-to-date information about this topic.
        Gather key technical details, examples, and best practices.
        Identify authoritative sources and recent developments.
        """,
        expected_output="Comprehensive research notes with key points and references",
        agent=researcher
    )
    
    writing_task = Task(
        description="""Using the research provided, write a comprehensive technical blog post.
        Structure the post with clear headings, introduction, and conclusion.
        Include code examples where appropriate.
        Explain technical concepts at the appropriate depth level.
        Format the post using markdown.
        """,
        expected_output="A well-structured technical blog post in markdown format",
        agent=writer,
        context=[research_task]  # This task depends on research task
    )
    
    # Create the crew
    crew = Crew(
        agents=[researcher, writer],
        tasks=[research_task, writing_task],
        verbose=True
    )
    
    return crew

def generate_blog_post(request: BlogRequest) -> dict:
    """Generate a blog post using a crew of AI agents"""
    try:
        # Check if API keys are set
        if not openai_api_key:
            return {"error": "OpenAI API key not set"}
            
        if not (os.getenv("GOOGLE_API_KEY") and os.getenv("GOOGLE_CSE_ID")):
            return {"error": "Google Search API credentials not set"}
        
        # Create and run the crew
        crew = create_blog_crew(request)
        result = crew.kickoff()
        
        # Return the result
        return {
            "title": request.topic,
            "content": result,
            "keywords": request.keywords,
            "depth": request.depth
        }
    except Exception as e:
        return {"error": f"Blog generation failed: {str(e)}"} 