import os
from typing import Dict, Optional
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class StyleEnhancer:
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key not found in environment variables")
        self.client = OpenAI(api_key=self.api_key)

    def transform_style(self, content: str, style: str) -> Dict:
        """
        Transform content to a different writing style.
        
        Args:
            content (str): The content to transform
            style (str): The target style (e.g., "professional", "technical", "casual")
            
        Returns:
            Dict: Contains transformed text and metadata
        """
        try:
            prompt = f"""Transform the following content to a {style} style while 
            maintaining technical accuracy and keeping the same information. 
            Make the transformation feel natural and engaging:

            Content: {content}
            
            Transformed content:"""

            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert content editor skilled in transforming text while maintaining technical accuracy."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )

            transformed_text = response.choices[0].message.content.strip()
            
            return {
                "success": True,
                "transformed_text": transformed_text,
                "original_text": content,
                "style": style,
                "error": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "transformed_text": None,
                "original_text": content,
                "style": style,
                "error": str(e)
            }

    def get_available_styles(self) -> list:
        """Return list of available transformation styles."""
        return [
            "Professional",
            "Technical",
            "Casual",
            "Tutorial-style",
            "Academic"
        ]
