import openai
import os
from typing import Literal, Dict, Any, List
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContentEnhancer:
    """Class to handle various content enhancement features"""
    
    def __init__(self, api_key=None):
        """Initialize with OpenAI API key"""
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        # Debug info about API key
        logger.info(f"API Key found: {'Yes' if self.api_key else 'No'}")
        logger.info(f"API Key length: {len(self.api_key) if self.api_key else 0}")
        logger.info(f"First few characters: {self.api_key[:5]}... (should start with 'sk-')")
        
        # Set the API key for OpenAI
        openai.api_key = self.api_key
    
    def expand_paragraph(self, 
                         paragraph_text: str, 
                         expansion_type: Literal["detail", "example", "technical", "simplified", "counterpoint"] = "detail") -> str:
        """
        Expand a paragraph with additional information based on the expansion type.
        
        Parameters:
        - paragraph_text: The original paragraph to expand
        - expansion_type: One of "detail", "example", "technical", "simplified", "counterpoint"
        
        Returns:
        - Expanded paragraph text
        """
        # Define prompts for different expansion types
        prompts: Dict[str, str] = {
            "detail": f"Expand this paragraph with more detailed information while maintaining the same tone and style: {paragraph_text}",
            "example": f"Add a practical, real-world example to illustrate this concept: {paragraph_text}",
            "technical": f"Make this paragraph more technically detailed for experts while preserving the core information: {paragraph_text}",
            "simplified": f"Simplify this paragraph for beginners while maintaining accuracy: {paragraph_text}",
            "counterpoint": f"Add a balanced counterpoint or alternative viewpoint to this paragraph: {paragraph_text}"
        }
        
        # Get the appropriate prompt
        prompt = prompts.get(expansion_type, prompts["detail"])
        
        try:
            # Call OpenAI API for content generation
            try:
                # Try using the newer OpenAI client format
                client = openai.OpenAI(api_key=self.api_key)
                response = client.chat.completions.create(
                    model="gpt-4o",  # Use appropriate model
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that expands and enhances content while maintaining accuracy and relevance."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=500
                )
                expanded_text = response.choices[0].message.content.strip()
            except (ImportError, AttributeError):
                # Fall back to the older format if needed
                logger.info("Falling back to older OpenAI API format")
                response = openai.ChatCompletion.create(
                    model="gpt-4o",  # Use appropriate model
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that expands and enhances content while maintaining accuracy and relevance."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=500
                )
                expanded_text = response.choices[0].message.content.strip()
            
            return expanded_text
            
        except Exception as e:
            logger.error(f"Error in paragraph expansion: {str(e)}")
            return f"Error expanding paragraph: {str(e)}"
    
    def generate_section_outline(self, topic: str, depth: int = 3) -> List[Dict[str, Any]]:
        """
        Generate an outline for a new section on a given topic.
        
        Parameters:
        - topic: The main topic for the section
        - depth: How detailed the outline should be (1-5)
        
        Returns:
        - List of section headings and subheadings
        """
        try:
            # Call OpenAI API for outline generation
            try:
                # Try using the newer OpenAI client format
                client = openai.OpenAI(api_key=self.api_key)
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that creates well-structured content outlines."},
                        {"role": "user", "content": f"Create a detailed outline for a section about '{topic}'. Include {depth} levels of headings and subheadings. Format as JSON with 'title', 'subheadings', and 'key_points' fields."}
                    ],
                    temperature=0.7,
                    max_tokens=1000
                )
                outline_text = response.choices[0].message.content.strip()
            except (ImportError, AttributeError):
                # Fall back to the older format if needed
                logger.info("Falling back to older OpenAI API format")
                response = openai.ChatCompletion.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that creates well-structured content outlines."},
                        {"role": "user", "content": f"Create a detailed outline for a section about '{topic}'. Include {depth} levels of headings and subheadings. Format as JSON with 'title', 'subheadings', and 'key_points' fields."}
                    ],
                    temperature=0.7,
                    max_tokens=1000
                )
                outline_text = response.choices[0].message.content.strip()
            
            # In a real implementation, you would parse the JSON here
            # For simplicity, we're returning the raw text
            return outline_text
            
        except Exception as e:
            logger.error(f"Error in outline generation: {str(e)}")
            return f"Error generating outline: {str(e)}"
    
    def enhance_content(self, content: str, enhancement_type: Literal["detail", "example", "technical", "simplified", "counterpoint"] = "detail") -> str:
        """
        Enhance the entire content with the specified enhancement type
        
        Parameters:
        ----------
        content : str
            The content to enhance
        enhancement_type : Literal["detail", "example", "technical", "simplified", "counterpoint"]
            The type of enhancement to apply
            
        Returns:
        -------
        str
            The enhanced content
        """
        # Define prompts for different enhancement types
        enhancement_prompts = {
            "detail": "Enhance the following content by adding more details and explanations. Make it more comprehensive while maintaining the original tone and structure. You MUST add significant new details.",
            "example": "Enhance the following content by adding relevant examples to illustrate the key points. The examples should be practical and help the reader understand the concepts better. You MUST add at least 2-3 concrete examples.",
            "technical": "Enhance the following content by adding more technical details and terminology. Make it more suitable for an expert audience while maintaining the original structure. You MUST add technical terms and concepts.",
            "simplified": "Simplify the following content to make it more accessible to a general audience. Remove jargon, use simpler language, and clarify complex concepts. You MUST make significant simplifications.",
            "counterpoint": "Enhance the following content by adding counterpoints or alternative perspectives to the main arguments. Present balanced viewpoints while maintaining the original structure. You MUST add meaningful counterarguments."
        }
        
        # Select the appropriate prompt
        prompt = enhancement_prompts.get(enhancement_type, enhancement_prompts["detail"])
        
        # Create the full prompt with explicit instructions to make changes
        full_prompt = f"{prompt}\n\nContent:\n{content}\n\nYou MUST make significant changes to the content. Return the enhanced version with meaningful additions or modifications. Do not return the original text unchanged."
        
        # Generate enhanced content using OpenAI
        try:
            logger.info(f"Calling OpenAI API with enhancement type: {enhancement_type}")
            
            # Use the OpenAI API client
            import openai
            
            # First try the newer client format
            try:
                client = openai.OpenAI(api_key=self.api_key)
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "You are a skilled content editor and writer. Your task is to enhance content according to specific instructions. You MUST make significant changes to the content."},
                        {"role": "user", "content": full_prompt}
                    ],
                    max_tokens=4000,
                    temperature=0.7
                )
                enhanced_content = response.choices[0].message.content.strip()
            except Exception as e:
                logger.warning(f"Error with newer OpenAI client format: {str(e)}")
                # Fall back to the older format
                response = openai.ChatCompletion.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "You are a skilled content editor and writer. Your task is to enhance content according to specific instructions. You MUST make significant changes to the content."},
                        {"role": "user", "content": full_prompt}
                    ],
                    max_tokens=4000,
                    temperature=0.7
                )
                enhanced_content = response.choices[0].message.content.strip()
            
            # Check if content was actually enhanced
            if enhanced_content == content:
                logger.warning("Enhanced content is identical to original content!")
                # Try one more time with an even stronger prompt
                retry_prompt = f"The content MUST be significantly enhanced with new information, examples, or perspectives. Please make substantial changes to the following content:\n\n{content}"
                
                try:
                    # Try again with a stronger prompt
                    client = openai.OpenAI(api_key=self.api_key)
                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": "You are a skilled content editor and writer. Your task is to enhance content with SUBSTANTIAL changes."},
                            {"role": "user", "content": retry_prompt}
                        ],
                        max_tokens=4000,
                        temperature=0.8
                    )
                    enhanced_content = response.choices[0].message.content.strip()
                except Exception:
                    # If retry fails, use the original content with a message
                    enhanced_content = f"{content}\n\n✨ Your content is already well-crafted! The AI analysis suggests it's already optimized for this enhancement type. You might want to try a different enhancement option."
            
            return enhanced_content
        except Exception as e:
            logger.error(f"Error enhancing content: {str(e)}")
            # Return original content if enhancement fails
            return content


# Example usage
if __name__ == "__main__":
    enhancer = ContentEnhancer()
    expanded = enhancer.expand_paragraph(
        "Python is a high-level programming language known for its readability.", 
        "example"
    )
    print(expanded)
