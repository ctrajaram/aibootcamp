"""
Content Verification module for hallucination-free responses.
This module provides a final verification layer before content is presented to users.
"""

import os
from typing import Dict, Any, List, Optional, Tuple, Union, Callable
from openai import OpenAI
import json
from app.agents.hallucination_checker import HallucinationChecker
from app.utils.content_processor import ContentProcessor
from app.utils.feedback_loop import FeedbackLoop

class ContentVerification:
    """
    Provides a final verification step to ensure content is hallucination-free.
    """
    
    def __init__(self, 
                model: str = "gpt-4o", 
                level: str = "standard",
                hallucination_checker = None,
                feedback_loop = None):
        """
        Initialize the ContentVerification system.
        
        Args:
            model: Model to use for verification
            level: Verification level - 'basic', 'standard', or 'high'
            hallucination_checker: Optional HallucinationChecker instance
            feedback_loop: Optional FeedbackLoop instance
        """
        print(f"Initializing ContentVerification with {level} level...")
        
        # Store configuration
        self.model = model
        self.verification_level = level
        
        # Set verification parameters based on level
        self._set_verification_parameters()
        
        # Initialize components
        self.hallucination_checker = hallucination_checker
        self.feedback_loop = feedback_loop
        
        # Load components if not provided
        if self.hallucination_checker is None:
            from app.agents.hallucination_checker import HallucinationChecker
            self.hallucination_checker = HallucinationChecker(model=model)
            print("Initializing HallucinationChecker...")
            
        if self.feedback_loop is None:
            from app.utils.content_processor import ContentProcessor
            from app.utils.feedback_loop import FeedbackLoop
            content_processor = ContentProcessor(model=model)
            self.feedback_loop = FeedbackLoop(
                hallucination_checker=self.hallucination_checker,
                content_processor=content_processor,
                max_iterations=self.max_iterations,
                model=model,
                target_score=self.target_score
            )
            print("Initializing FeedbackLoop...")
        
        # Initialize OpenAI client
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        
        self.client = OpenAI(api_key=openai_api_key)
        
    def _set_verification_parameters(self):
        """Set verification parameters based on verification level."""
        if self.verification_level == "strict":
            self.target_score = 0.98
            self.max_iterations = 5
            self.verification_threshold = 0.95
            self.auto_improve = True
        elif self.verification_level == "relaxed":
            self.target_score = 0.9
            self.max_iterations = 2
            self.verification_threshold = 0.85
            self.auto_improve = True
        else:  # standard
            self.target_score = 0.95
            self.max_iterations = 3
            self.verification_threshold = 0.9
            self.auto_improve = True
            
    def verify_content(self, query: str, response: str, 
                      web_search_results: str, sources: List[str],
                      allow_improvement: bool = True,
                      callback: Optional[Callable[[str], None]] = None) -> Dict[str, Any]:
        """
        Verify content for hallucinations and improve if needed.
        
        Args:
            query: The original query that prompted the response
            response: The response to verify
            web_search_results: Raw web search results text
            sources: List of source URLs
            allow_improvement: Whether to allow automatic improvement if verification fails
            callback: Optional callback function to report progress
            
        Returns:
            Dictionary containing verification results and improved content if applicable
        """
        print(f"Verifying content for hallucinations, level={self.verification_level}...")
        
        if callback:
            callback(f"Verifying content against sources, level={self.verification_level}...")
        
        # Initial evaluation
        evaluation = self.hallucination_checker.evaluate_response(
            query, response, web_search_results, sources
        )
        
        current_score = evaluation.get("faithfulness_score", 0)
        verification_passed = current_score >= self.verification_threshold
        
        result = {
            "verification_passed": verification_passed,
            "score": current_score,
            "threshold": self.verification_threshold,
            "level": self.verification_level,
            "original_content": response,
            "final_content": response,  # Default to original
            "final_score": current_score,  # Default to initial score
            "verification_details": evaluation,
            "improvement_performed": False,
            "iterations": 0
        }
        
        # If verification passed, return result
        if verification_passed:
            print(f"Content passed verification: score={current_score:.3f} >= threshold={self.verification_threshold}")
            return result
            
        # If verification failed and auto-improvement is allowed
        if not verification_passed and allow_improvement and self.auto_improve:
            print(f"Content failed verification (score={current_score:.3f}). Attempting improvement...")
            
            # Use feedback loop to improve content
            improvement_result = self.feedback_loop.improve_content(
                query, response, web_search_results, sources, callback=callback
            )
            
            # Get the improved content
            improved_content = improvement_result.get("improved_content", response)
            final_score = improvement_result.get("final_score", current_score)
            improvement_iterations = improvement_result.get("iterations", 0)
            
            # Check if improvement actually improved the content
            improvement_delta = final_score - current_score
            meaningful_improvement = improvement_delta > 0.05
            
            # Update result with improvement data
            result["improvement_performed"] = True
            result["final_content"] = improved_content
            result["improvement_details"] = improvement_result
            result["iterations"] = improvement_iterations
            result["final_score"] = final_score
            result["improvement_delta"] = improvement_delta
            result["metrics"] = improvement_result.get("metrics", [])
            
            # Check if the improved content passes verification
            verification_passed = final_score >= self.verification_threshold
            result["verification_passed"] = verification_passed
            
            status_message = (
                f"Content improvement complete: initial={current_score:.3f}, final={final_score:.3f}"
            )
            print(status_message)
            if callback:
                callback(status_message)
            
        return result
        
    def add_verification_metadata(self, content: str, verification_result: Dict[str, Any]) -> str:
        """
        Add verification metadata to content for transparency.
        
        Args:
            content: The verified content
            verification_result: The result from verify_content method
            
        Returns:
            Content with added verification metadata
        """
        # Only add metadata if verification was performed
        if not verification_result:
            return content
            
        # Extract key verification metrics
        score = verification_result.get("final_score", verification_result.get("score", 0))
        passed = verification_result.get("final_verification_passed", 
                                       verification_result.get("verification_passed", False))
        improved = verification_result.get("improvement_performed", False)
        
        # Format score as percentage
        score_percent = int(score * 100)
        
        # Create verification footer
        verification_status = "[VERIFIED]" if passed else "[WARNING: May contain inaccuracies]"
        improvement_status = "[Auto-improved]" if improved else ""
        
        footer = f"""
---
*Content {verification_status} ({score_percent}% factual accuracy) {improvement_status}*
"""
        
        return content + footer
        
    def get_verification_badge(self, verification_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a verification badge for UI display.
        
        Args:
            verification_result: The result from verify_content method
            
        Returns:
            Dictionary with badge details for UI rendering
        """
        # Extract key verification metrics
        score = verification_result.get("final_score", verification_result.get("score", 0))
        passed = verification_result.get("final_verification_passed", 
                                       verification_result.get("verification_passed", False))
        improved = verification_result.get("improvement_performed", False)
        
        # Format score as percentage
        score_percent = int(score * 100)
        
        # Determine badge color based on score
        if score >= 0.95:
            color = "green"
            emoji = "[OK]"
        elif score >= 0.85:
            color = "yellow"
            emoji = "[WARNING]"
        else:
            color = "red"
            emoji = "[ERROR]"
            
        # Create badge text
        if passed and improved:
            text = f"{emoji} Verified & Auto-improved"
        elif passed:
            text = f"{emoji} Verified"
        elif improved:
            text = f"{emoji} Auto-improved but may contain inaccuracies"
        else:
            text = f"{emoji} May contain inaccuracies"
            
        return {
            "text": text,
            "color": color,
            "score": score_percent,
            "passed": passed,
            "improved": improved
        }
