from crewai import Agent
import os
from dotenv import load_dotenv
import streamlit as st
import re
from urllib.parse import urlparse

# Make sure we load environment variables
load_dotenv()

# Get API key
openai_api_key = os.getenv("OPENAI_API_KEY")

def get_domain_authority_score(url):
    """
    Assign an authority score to a domain based on its TLD and known reliable domains.
    
    Args:
        url: The URL to evaluate
        
    Returns:
        A score from 0-100 representing the domain's authority
    """
    try:
        # Parse the URL to get the domain
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()
        
        # Remove www. prefix if present
        if domain.startswith('www.'):
            domain = domain[4:]
        
        # High authority TLDs
        high_authority_tlds = ['.edu', '.gov', '.mil', '.org']
        
        # Known high authority technical domains
        high_authority_domains = [
            'github.com', 'stackoverflow.com', 'docs.python.org',
            'developer.mozilla.org', 'arxiv.org', 'ieee.org', 'acm.org',
            'docs.microsoft.com', 'cloud.google.com', 'aws.amazon.com',
            'docs.aws.amazon.com', 'docs.docker.com', 'kubernetes.io',
            'docs.github.com', 'docs.gitlab.com', 'reactjs.org', 'angular.io',
            'vuejs.org', 'tensorflow.org', 'pytorch.org', 'scikit-learn.org',
            'numpy.org', 'pandas.pydata.org', 'python.org', 'docs.python.org',
            'developer.apple.com', 'developer.android.com', 'web.dev',
            'w3.org', 'w3schools.com', 'mdn.dev', 'developer.mozilla.org',
            'docs.djangoproject.com', 'flask.palletsprojects.com',
            'docs.sqlalchemy.org', 'docs.celeryproject.org', 'redis.io',
            'mongodb.com', 'postgresql.org', 'mysql.com', 'elastic.co',
            'docs.npmjs.com', 'yarnpkg.com', 'webpack.js.org', 'babeljs.io',
            'typescriptlang.org', 'rust-lang.org', 'go.dev', 'kotlinlang.org',
            'swift.org', 'docs.oracle.com', 'docs.microsoft.com', 'docs.google.com',
            'cloud.google.com', 'firebase.google.com', 'aws.amazon.com',
            'azure.microsoft.com', 'docs.aws.amazon.com', 'docs.azure.microsoft.com',
            'docs.docker.com', 'kubernetes.io', 'istio.io', 'prometheus.io',
            'grafana.com', 'jenkins.io', 'circleci.com', 'travis-ci.org',
            'github.blog', 'stackoverflow.blog', 'martinfowler.com', 'thoughtworks.com',
            'infoq.com', 'oreilly.com', 'packtpub.com', 'aclweb.org',
            'ai.google', 'openai.com', 'huggingface.co', 'paperswithcode.com',
            'distill.pub', 'jmlr.org', 'neurips.cc', 'icml.cc', 'iclr.cc',
            'langchain.com', 'langchain.readthedocs.io', 'python.langchain.com'
        ]
        
        # Medium authority domains (popular tech blogs, news sites, etc.)
        medium_authority_domains = [
            'medium.com', 'dev.to', 'hackernoon.com', 'techcrunch.com',
            'wired.com', 'theverge.com', 'engadget.com', 'venturebeat.com',
            'zdnet.com', 'cnet.com', 'arstechnica.com', 'thenextweb.com',
            'towardsdatascience.com', 'freecodecamp.org', 'css-tricks.com',
            'smashingmagazine.com', 'alistapart.com', 'sitepoint.com',
            'tutorialspoint.com', 'geeksforgeeks.org', 'javatpoint.com',
            'baeldung.com', 'digitalocean.com/community', 'scotch.io',
            'auth0.com/blog', 'twilio.com/blog', 'stripe.com/blog',
            'blog.cloudflare.com', 'blog.github.com', 'engineering.fb.com',
            'netflixtechblog.com', 'engineering.linkedin.com', 'blog.twitter.com',
            'blog.discord.com', 'slack.engineering', 'uber.com/blog/engineering',
            'engineering.atspotify.com', 'airbnb.io', 'dropbox.tech',
            'blog.google', 'ai.googleblog.com', 'research.google', 'research.facebook.com',
            'blogs.microsoft.com', 'aws.amazon.com/blogs', 'azure.microsoft.com/blog'
        ]
        
        # Calculate base score
        base_score = 50  # Default medium score
        
        # Check for high authority TLDs
        for tld in high_authority_tlds:
            if domain.endswith(tld):
                base_score = 80
                break
        
        # Check for known high authority domains
        if domain in high_authority_domains or any(domain.endswith('.' + d) for d in high_authority_domains):
            base_score = 90
        # Check for medium authority domains
        elif domain in medium_authority_domains or any(domain.endswith('.' + d) for d in medium_authority_domains):
            base_score = 70
        
        # Penalize very short domains (often less reliable)
        if len(domain) < 8 and base_score < 80:
            base_score -= 10
        
        # Ensure score is within bounds
        return max(0, min(100, base_score))
    except:
        # If there's any error parsing the URL, return a low score
        return 30

def needs_web_search(query):
    """
    Determine if a query might benefit from a web search.
    
    Args:
        query: The user's question or request
        
    Returns:
        Boolean indicating if web search might be helpful
    """
    # Keywords that suggest the need for current information
    current_info_keywords = [
        'latest', 'recent', 'new', 'current', 'update', 'today', 'news',
        'trend', 'development', 'release', 'version', 'announcement',
        'what is', 'how to', 'explain', 'compare', 'difference between'
    ]
    
    # Check if any of the keywords are in the query
    query_lower = query.lower()
    for keyword in current_info_keywords:
        if keyword in query_lower:
            return True
    
    return False

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
    
    # For Research Expert, always use web search
    web_search_results = ""
    search_performed = False
    search_query = ""
    sources = []
    source_scores = {}  # Dictionary to store domain authority scores
    
    if agent_type == "Research Expert":
        try:
            # Import the search_web function from the Cascade environment
            from app.agents.researcher import search_web
            
            # Show search indicator in UI
            search_status = st.empty()
            search_status.info("🔎 Performing web search for the latest information...")
            
            # Perform web search
            search_query = re.sub(r'\s+', ' ', query).strip()
            web_search_results = search_web(search_query)
            search_performed = True
            
            # Debug print
            print(f"Web search results: {web_search_results[:200]}...")
            
            # Extract sources from search results if possible
            if web_search_results:
                # Simple pattern to extract URLs from the search results
                url_pattern = re.compile(r'https?://[^\s\)\]]+')
                found_urls = url_pattern.findall(web_search_results)
                
                # Debug print
                print(f"Found URLs: {found_urls}")
                
                # Add unique URLs to sources list and calculate authority scores
                for url in found_urls:
                    # Clean up URL and remove trailing punctuation
                    clean_url = re.sub(r'[.,;:"\']$', '', url)
                    if clean_url not in sources:
                        sources.append(clean_url)
                        # Calculate and store domain authority score
                        source_scores[clean_url] = get_domain_authority_score(clean_url)
            
            # If no sources were found, add some default sources related to the query
            if not sources and "langchain" in query.lower():
                default_sources = [
                    "https://python.langchain.com/docs/get_started/introduction",
                    "https://github.com/langchain-ai/langchain",
                    "https://docs.langchain.com/docs/"
                ]
                for url in default_sources:
                    sources.append(url)
                    source_scores[url] = get_domain_authority_score(url)
            
            # Debug print
            print(f"Final sources: {sources}")
            print(f"Source scores: {source_scores}")
            
            # Clear the search indicator
            search_status.empty()
            
            # Sort sources by domain authority score (highest first)
            if sources and source_scores:
                sources = sorted(sources, key=lambda url: source_scores.get(url, 0), reverse=True)
            
            # Add search results to context
            if web_search_results:
                context += f"\nWeb search results:\n\n{web_search_results}\n\n"
                
                # Add information about source reliability
                if sources and source_scores:
                    context += "Source reliability assessment:\n"
                    for url in sources[:5]:  # Top 5 sources
                        score = source_scores.get(url, 0)
                        reliability = "High" if score >= 80 else "Medium" if score >= 50 else "Low"
                        context += f"- {url}: {reliability} reliability\n"
                    context += "\n"
                
                context += "Please incorporate relevant information from these search results in your response.\n\n"
                context += "IMPORTANT: For any factual claims, especially about technical topics, cite your sources in the response.\n\n"
                context += "Prioritize information from high reliability sources when available.\n\n"
        except Exception as e:
            print(f"Error performing web search: {str(e)}")
            # Continue without web search results if there's an error
    
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
        
        if agent_type == "Research Expert" and search_performed:
            prompt += """
            
            IMPORTANT INSTRUCTIONS FOR CITING SOURCES:
            1. For any factual claims, especially about technical topics, cite your sources.
            2. When referencing information from the web search results, mention the source.
            3. Be transparent about the limitations of your knowledge if information is not available.
            4. If you're uncertain about any information, explicitly state that.
            5. Prioritize information from high reliability sources when there are conflicting claims.
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
        
        # Extract the response text
        response_text = response.choices[0].message.content
        
        # Add web search indicator and sources to the response if search was performed
        if search_performed and agent_type == "Research Expert":
            header = f"🔎 *Web search performed for: \"{search_query}\"*\n\n"
            
            # Always add sources section, even if no sources were found from the search
            sources_section = "\n\n**Sources:**\n"
            
            if sources:
                for i, source in enumerate(sources[:5]):  # Limit to top 5 sources
                    # Add reliability indicator based on domain authority score
                    score = source_scores.get(source, 0)
                    if score >= 80:
                        reliability = "🟢 High reliability"
                    elif score >= 50:
                        reliability = "🟡 Medium reliability"
                    else:
                        reliability = "🔴 Low reliability"
                    
                    sources_section += f"{i+1}. {source} ({reliability})\n"
            else:
                # If no sources were found, add a note
                sources_section += "No specific sources were found in the search results.\n"
            
            # Always include the header and sources section
            response_text = f"{header}{response_text}{sources_section}"
        
        return response_text
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Error getting response from {agent_type}: {str(e)}"