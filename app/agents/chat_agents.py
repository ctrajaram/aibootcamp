from crewai import Agent
import os
from dotenv import load_dotenv
import streamlit as st

# Make sure we load environment variables
load_dotenv()

# Get API key
openai_api_key = os.getenv("OPENAI_API_KEY")

def create_research_expert():
    """
    Creates a research expert agent specialized in finding information.
    """
    return Agent(
        role='Research Expert',
        goal='Find accurate and comprehensive information on technical topics',
        backstory="""You are a seasoned research specialist with decades of experience in 
        technical fields. You have access to vast knowledge about software development, 
        technology trends, and computer science. You excel at finding specific information
        and explaining complex topics in an accessible way.""",
        verbose=True,
        allow_delegation=False,
        llm_config={
            "config_list": [{"model": "gpt-4o", "api_key": openai_api_key}],
            "temperature": 0.4
        }
    )

def create_editor_agent():
    """
    Creates an editor agent specialized in improving writing quality.
    """
    return Agent(
        role='Content Editor',
        goal='Improve the clarity, structure, and readability of technical content',
        backstory="""You are an experienced editor who has worked with major technical 
        publications. You have a keen eye for structure, flow, and narrative. You can 
        transform rough drafts into polished, professional content while maintaining 
        technical accuracy. You excel at suggesting improvements to make content more 
        engaging and accessible.""",
        verbose=True,
        allow_delegation=False,
        llm_config={
            "config_list": [{"model": "gpt-4o", "api_key": openai_api_key}],
            "temperature": 0.3
        }
    )

def create_technical_reviewer():
    """
    Creates a technical reviewer agent specialized in ensuring accuracy.
    """
    return Agent(
        role='Technical Reviewer',
        goal='Ensure technical accuracy and best practices in content',
        backstory="""You are a senior software engineer and technical architect with 
        experience across multiple domains. You have a deep understanding of programming 
        languages, frameworks, and system design. You can spot technical inaccuracies, 
        outdated practices, and security issues. You provide constructive feedback to 
        improve the technical quality of content.""",
        verbose=True,
        allow_delegation=False,
        llm_config={
            "config_list": [{"model": "gpt-4o", "api_key": openai_api_key}],
            "temperature": 0.2
        }
    )

def create_seo_specialist():
    """
    Creates an SEO specialist agent to optimize content for search engines.
    """
    return Agent(
        role='SEO Specialist',
        goal='Optimize content for search engines while maintaining quality',
        backstory="""You are an SEO expert with years of experience in content optimization. 
        You understand how search engines rank technical content and know the best practices 
        for improving visibility. You can suggest keywords, meta descriptions, and structural 
        changes to improve search rankings without compromising the quality or accuracy of 
        the content.""",
        verbose=True,
        allow_delegation=False,
        llm_config={
            "config_list": [{"model": "gpt-4o", "api_key": openai_api_key}],
            "temperature": 0.3
        }
    )

def get_agent_response(agent_type, query, blog_content=None):
    """
    Get a response from the specified agent type based on the user query.
    
    Args:
        agent_type: The type of agent to use (research, editor, technical, seo)
        query: The user's question or request
        blog_content: Optional current blog content for context
        
    Returns:
        The agent's response as a string
    """
    # Create the appropriate agent based on type
    if agent_type == "Research Expert":
        agent = create_research_expert()
    elif agent_type == "Content Editor":
        agent = create_editor_agent()
    elif agent_type == "Technical Reviewer":
        agent = create_technical_reviewer()
    elif agent_type == "SEO Specialist":
        agent = create_seo_specialist()
    else:
        return "Unknown agent type selected."
    
    # Prepare context for the agent
    context = ""
    if blog_content:
        context = f"\nHere is the current blog content for reference:\n\n{blog_content}\n\n"
    
    # Get response from the agent
    try:
        # Import the OpenAI client directly for generating responses
        from openai import OpenAI
        
        # Initialize the OpenAI client with the API key
        client = OpenAI(api_key=openai_api_key)
        
        # Create the prompt for the agent
        prompt = f"""As a {agent.role} with the following backstory:
        
        {agent.backstory}
        
        Your goal is: {agent.goal}
        
        Please respond to the following query:
        
        {query}
        
        {context}
        
        Provide a helpful, accurate, and concise response based on your expertise.
        """
        
        # Generate response using the OpenAI API directly
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": query}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        
        # Extract and return the response text
        return response.choices[0].message.content
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Error getting response from {agent_type}: {str(e)}" 