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
            response = openai.ChatCompletion.create(
                model="gpt-4o",  # Use appropriate model
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that expands and enhances content while maintaining accuracy and relevance."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.7
            )
            
            # Extract the generated text
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
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that creates well-structured content outlines."},
                    {"role": "user", "content": f"Create a detailed outline for a section about '{topic}'. Include {depth} levels of headings and subheadings. Format as JSON with 'title', 'subheadings', and 'key_points' fields."}
                ],
                max_tokens=1500,
                temperature=0.7
            )
            
            # Extract and parse the generated outline
            outline_text = response.choices[0].message.content.strip()
            
            # In a real implementation, you would parse the JSON here
            # For simplicity, we're returning the raw text
            return outline_text
            
        except Exception as e:
            logger.error(f"Error in outline generation: {str(e)}")
            return f"Error generating outline: {str(e)}"


# Example usage
if __name__ == "__main__":
    enhancer = ContentEnhancer()
    expanded = enhancer.expand_paragraph(
        "Python is a high-level programming language known for its readability.", 
        "example"
    )
    print(expanded)
