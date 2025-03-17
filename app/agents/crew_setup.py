from crewai import Agent, Task, Crew, Process
from langchain_community.utilities import GoogleSearchAPIWrapper
import os
from dotenv import load_dotenv
import openai
import time

# Make sure we load environment variables
load_dotenv()

# Explicitly set OpenAI API key
openai_api_key = os.getenv("OPENAI_API_KEY")
os.environ["OPENAI_API_KEY"] = openai_api_key
openai.api_key = openai_api_key

def create_researcher_agent() -> Agent:
    """
    Create a specialized research agent focused on gathering accurate information.
    """
    return Agent(
        role='Technical Research Specialist',
        goal='Gather comprehensive and accurate information about technical topics',
        backstory="""You are an expert technical researcher with a background in 
        computer science and software engineering. You excel at finding accurate, 
        up-to-date information about technical topics from reliable sources. 
        You're meticulous about verifying facts and collecting diverse perspectives.""",
        verbose=True,
        allow_delegation=False,
        # Configure the language model
        llm_config={
            "config_list": [{"model": "gpt-4o", "api_key": openai_api_key}],
            "temperature": 0.4,  # Lower temperature for factual research
            "request_timeout": 120
        }
    )

def create_outline_agent() -> Agent:
    """
    Create a specialized agent for creating well-structured outlines.
    """
    return Agent(
        role='Content Outline Strategist',
        goal='Create comprehensive, logical outlines for technical blog posts',
        backstory="""You are an expert at organizing technical information into 
        clear, logical structures. With your background in technical writing and 
        information architecture, you excel at creating outlines that flow naturally 
        and cover all important aspects of a topic. You understand how to structure 
        content for different technical levels and learning styles.""",
        verbose=True,
        allow_delegation=False,
        # Configure the language model
        llm_config={
            "config_list": [{"model": "gpt-4o", "api_key": openai_api_key}],
            "temperature": 0.5,
            "request_timeout": 120
        }
    )

def create_writer_agent() -> Agent:
    """
    Create a specialized agent for writing technical content.
    """
    return Agent(
        role='Technical Content Writer',
        goal='Transform outlines into engaging, informative technical blog posts',
        backstory="""You are a skilled technical writer with expertise in explaining 
        complex concepts clearly and engagingly. You have a talent for making technical 
        subjects accessible while maintaining accuracy. You write with a conversational 
        yet professional tone and know how to include relevant code examples, diagrams, 
        and explanations that resonate with technical audiences.""",
        verbose=True,
        allow_delegation=False,
        # Configure the language model
        llm_config={
            "config_list": [{"model": "gpt-4o", "api_key": openai_api_key}],
            "temperature": 0.7,  # Higher temperature for creative writing
            "request_timeout": 120
        }
    )

def create_editor_agent() -> Agent:
    """
    Create a specialized agent for editing and polishing content.
    """
    return Agent(
        role='Technical Editor and Quality Assurance',
        goal='Ensure technical accuracy, clarity, and polish in the final content',
        backstory="""You are a meticulous technical editor with an eye for detail 
        and accuracy. With your background in both technical subjects and professional 
        editing, you excel at improving content clarity, fixing technical inaccuracies, 
        and ensuring code examples work correctly. You also check for consistent formatting, 
        logical flow, and appropriate technical depth for the target audience.""",
        verbose=True,
        allow_delegation=False,
        # Configure the language model
        llm_config={
            "config_list": [{"model": "gpt-4o", "api_key": openai_api_key}],
            "temperature": 0.3,  # Lower temperature for precise editing
            "request_timeout": 120
        }
    )

def create_qa_agent() -> Agent:
    """
    Create a specialized agent for final quality assurance.
    """
    return Agent(
        role='Technical Quality Assurance Specialist',
        goal='Perform comprehensive quality checks on technical content',
        backstory="""You are a meticulous technical quality assurance specialist with 
        extensive experience in technical content evaluation. You have a keen eye for 
        technical inaccuracies, logical inconsistencies, and content gaps. You're known 
        for your ability to identify potential issues that others might miss and ensure 
        that technical content meets the highest standards of accuracy, clarity, and 
        completeness. You also verify that code examples are correct and follow best practices.""",
        verbose=True,
        allow_delegation=False,
        # Configure the language model
        llm_config={
            "config_list": [{"model": "gpt-4o", "api_key": openai_api_key}],
            "temperature": 0.2,  # Very low temperature for critical evaluation
            "request_timeout": 120
        }
    )

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

def create_blog_crew(topic_title: str, keywords: list, depth: str, progress_callback=None) -> Crew:
    """
    Create a crew of specialized agents for blog post generation.
    
    Args:
        topic_title: The main topic title
        keywords: List of keywords related to the topic
        depth: The technical depth level (beginner, intermediate, advanced)
        progress_callback: Optional callback function to report progress
        
    Returns:
        A CrewAI Crew object configured with specialized agents and tasks
    """
    # Format keywords for better readability
    keywords_str = ', '.join(keywords) if keywords else "general overview"
    
    # Create the specialized agents
    researcher = create_researcher_agent()
    outline_creator = create_outline_agent()
    writer = create_writer_agent()
    editor = create_editor_agent()
    qa_specialist = create_qa_agent()
    
    # Perform initial web searches to gather information
    search_results = []
    search_queries = [
        f"{topic_title} overview",
        f"{topic_title} {keywords_str}",
        f"{topic_title} tutorial {depth} level",
        f"{topic_title} best practices 2023",
        f"{topic_title} code examples"
    ]
    
    print("Performing initial web searches...")
    if progress_callback:
        progress_callback(0.1, "Starting web searches...")
        
    total_queries = len(search_queries)
    for i, query in enumerate(search_queries):
        if progress_callback:
            progress_callback(0.1 + (i / total_queries * 0.3), f"Searching: {query}")
            
        result = search_web(query)
        search_results.append(f"Query: {query}\n{result}\n")
        
        if progress_callback:
            progress_callback(0.1 + ((i + 1) / total_queries * 0.3), f"Completed search {i+1}/{total_queries}")
    
    combined_search_results = "\n".join(search_results)
    print(f"Completed {len(search_queries)} web searches")
    
    # Define a callback for task completion to update progress
    def task_callback(task_output):
        # Get the task name from the task_output
        # In the new API, we need to check the structure of task_output
        try:
            # Try to get agent information from the task output
            agent_role = None
            
            if hasattr(task_output, 'agent'):
                agent_role = task_output.agent.role
                print(f"Found agent role from task_output.agent.role: {agent_role}")
            elif hasattr(task_output, 'agent_name'):
                agent_role = task_output.agent_name
                print(f"Found agent role from task_output.agent_name: {agent_role}")
            elif hasattr(task_output, 'task') and hasattr(task_output.task, 'agent'):
                agent_role = task_output.task.agent.role
                print(f"Found agent role from task_output.task.agent.role: {agent_role}")
            else:
                print("Could not determine agent role from task_output")
                # Try to infer from the task description if available
                if hasattr(task_output, 'task_description'):
                    desc = task_output.task_description
                    if "research" in desc.lower():
                        agent_role = "Research Specialist"
                    elif "outline" in desc.lower():
                        agent_role = "Outline Strategist"
                    elif "write" in desc.lower():
                        agent_role = "Content Writer"
                    elif "edit" in desc.lower():
                        agent_role = "Editor"
                    elif "quality" in desc.lower() or "qa" in desc.lower():
                        agent_role = "Quality Assurance"
                    
                    if agent_role:
                        print(f"Inferred agent role from task description: {agent_role}")
            
            if not agent_role:
                # If we can't determine the agent, use a default progression
                current_progress = 0.5
                current_message = "Processing content..."
                
                # Check if we're at the beginning or end of the process
                if progress_callback:
                    if current_progress < 0.2:
                        progress_callback(0.5, "Research complete. Creating outline...")
                    elif current_progress > 0.8:
                        progress_callback(0.95, "QA complete. Finalizing blog post...")
                    else:
                        progress_callback(current_progress, current_message)
                return
                
            # Update progress based on agent role - only major transitions
            if "Research" in agent_role:
                if progress_callback:
                    print("Updating progress: Research complete")
                    progress_callback(0.5, "Research complete. Creating outline...")
            elif "Outline" in agent_role:
                if progress_callback:
                    print("Updating progress: Outline complete")
                    progress_callback(0.6, "Outline complete. Writing content...")
            elif "Writer" in agent_role or "Content Writer" in agent_role:
                if progress_callback:
                    print("Updating progress: Writing complete")
                    progress_callback(0.75, "Draft complete. Editing content...")
            elif "Editor" in agent_role:
                if progress_callback:
                    print("Updating progress: Editing complete")
                    progress_callback(0.85, "Editing complete. Performing final QA...")
            elif "Quality" in agent_role:
                if progress_callback:
                    print("Updating progress: QA complete")
                    progress_callback(0.95, "QA complete. Finalizing blog post...")
        except Exception as e:
            # If there's an error in the callback, log it but don't fail the process
            print(f"Error in task callback: {str(e)}")
            import traceback
            traceback.print_exc()
            # Still try to update progress
            if progress_callback:
                progress_callback(0.7, "Processing content...")
    
    # Create tasks for each agent
    research_task = Task(
        description=f"""Research the technical topic: "{topic_title}" thoroughly.
        
        Focus on these keywords: {keywords_str}
        Technical depth level: {depth}
        
        I've already performed some web searches for you. Here are the results:
        
        {combined_search_results}
        
        Based on this information and your knowledge, compile a comprehensive research report that includes:
        1. Key concepts and definitions
        2. Current best practices and methodologies
        3. Common use cases and applications
        4. Recent developments or trends
        5. Technical challenges and solutions
        6. References to authoritative sources
        
        Your research will be used to create an outline for a technical blog post, so focus on gathering 
        accurate, relevant, and well-organized information.
        """,
        expected_output="A comprehensive research report with accurate information, organized by subtopics.",
        agent=researcher,
        # Use on_task_complete instead of callback
        on_task_complete=task_callback
    )
    
    outline_task = Task(
        description=f"""Create a detailed outline for a technical blog post about "{topic_title}".
        
        The blog post should be targeted at a {depth} level audience.
        Focus on these keywords: {keywords_str}
        
        Use the research report provided by the Technical Research Specialist:
        
        {{research_task.output}}
        
        Create a logical, comprehensive outline that includes:
        1. An engaging introduction that explains why this topic matters
        2. Clear section headings and subheadings
        3. Bullet points for key content to include in each section
        4. Places where code examples would be beneficial
        5. A conclusion section that summarizes key takeaways
        
        The outline should follow a logical progression that builds understanding from the ground up,
        appropriate for the {depth} technical level.
        """,
        expected_output="A detailed, well-structured outline for a technical blog post.",
        agent=outline_creator,
        context=[research_task],
        # Use on_task_complete instead of callback
        on_task_complete=task_callback
    )
    
    writing_task = Task(
        description=f"""Write a comprehensive technical blog post about "{topic_title}" based on the outline provided.
        
        The blog post should be targeted at a {depth} level audience.
        Focus on these keywords: {keywords_str}
        
        Use the outline created by the Content Outline Strategist:
        
        {{outline_task.output}}
        
        Transform this outline into a complete, engaging blog post that:
        1. Uses a conversational yet professional tone
        2. Explains technical concepts clearly with examples
        3. Includes relevant code snippets where appropriate
        4. Uses markdown formatting for headings, code blocks, etc.
        5. Maintains technical accuracy while being accessible
        6. Has a logical flow that builds understanding progressively
        
        The final blog post should be comprehensive, informative, and engaging for a {depth} level technical audience.
        """,
        expected_output="A complete, well-written technical blog post in markdown format.",
        agent=writer,
        context=[outline_task],
        # Use on_task_complete instead of callback
        on_task_complete=task_callback
    )
    
    editing_task = Task(
        description=f"""Review and improve the technical blog post about "{topic_title}".
        
        The blog post is targeted at a {depth} level audience.
        Focus on these keywords: {keywords_str}
        
        Here is the draft blog post from the Technical Content Writer:
        
        {{writing_task.output}}
        
        Your job is to:
        1. Ensure technical accuracy of all information
        2. Improve clarity and readability
        3. Check that code examples are correct and well-explained
        4. Verify that the content is appropriate for a {depth} level audience
        5. Add any missing important information
        6. Ensure consistent formatting and style
        7. Polish the introduction and conclusion
        
        Provide the edited version of the blog post in markdown format.
        """,
        expected_output="An edited, technically accurate blog post.",
        agent=editor,
        context=[writing_task],
        # Use on_task_complete instead of callback
        on_task_complete=task_callback
    )
    
    qa_task = Task(
        description=f"""Perform a comprehensive quality assessment of this technical blog post about "{topic_title}".
        
        The blog post is targeted at a {depth} level audience.
        Focus on these keywords: {keywords_str}
        
        Here is the edited blog post:
        
        {{editing_task.output}}
        
        Your job is to perform a thorough quality check:
        1. Verify all technical information for accuracy
        2. Ensure all code examples are correct, efficient, and follow best practices
        3. Check that the content addresses all the important aspects of the topic
        4. Verify the content is appropriate for the {depth} level audience
        5. Ensure the blog post covers all the specified keywords: {keywords_str}
        6. Check for any logical inconsistencies or gaps in explanations
        7. Verify that examples and use cases are relevant and helpful
        8. Ensure the content is well-structured with a clear flow
        
        If you find any issues, fix them directly and provide the final, polished version of the blog post.
        If no issues are found, you can make minor improvements and return the final version.
        
        Provide the final, quality-assured blog post in markdown format.
        """,
        expected_output="A final, quality-assured blog post ready for publication.",
        agent=qa_specialist,
        context=[editing_task],
        # Use on_task_complete instead of callback
        on_task_complete=task_callback
    )
    
    # Create the crew with the agents and tasks
    crew = Crew(
        agents=[researcher, outline_creator, writer, editor, qa_specialist],
        tasks=[research_task, outline_task, writing_task, editing_task, qa_task],
        verbose=True,  # Changed from 2 to True
        process=Process.sequential  # Execute tasks in sequence
    )
    
    return crew 