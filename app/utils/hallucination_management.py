"""
Hallucination Management System - Integration Module
This module demonstrates how to use the hallucination management components 
to create hallucination-free content in a complete workflow.
"""

import os
from typing import List, Dict, Any, Optional, Callable, Union

from app.agents.hallucination_checker import HallucinationChecker
from app.utils.content_processor import ContentProcessor
from app.utils.feedback_loop import FeedbackLoop
from app.utils.content_verification import ContentVerification

class HallucinationManagement:
    """
    End-to-end hallucination management system that integrates detection, 
    correction, and verification of content.
    """
    
    def __init__(self, 
                model: str = "gpt-4o", 
                level: str = "standard",
                content_processor: ContentProcessor = None,
                hallucination_checker: HallucinationChecker = None):
        """
        Initialize the hallucination management system.
        
        Args:
            model: Model to use for hallucination detection and correction
            level: Verification level - 'basic', 'standard', or 'high'
            content_processor: Optional ContentProcessor instance
            hallucination_checker: Optional HallucinationChecker instance
        """
        print(f"Initializing HallucinationManagement system (level: {level})...")
        
        # Initialize components
        self.hallucination_checker = hallucination_checker or HallucinationChecker(model=model)
        self.content_processor = content_processor or ContentProcessor(model=model)
        
        # Create feedback loop with our components
        self.feedback_loop = FeedbackLoop(
            hallucination_checker=self.hallucination_checker,
            content_processor=self.content_processor
        )
        
        # Initialize content verification with appropriate level
        self.content_verification = ContentVerification(
            level=level,
            hallucination_checker=self.hallucination_checker,
            feedback_loop=self.feedback_loop
        )
        
        # Configuration
        self.level = level
        self.model = model
    
    def process_content(self, 
                       query: str, 
                       content: str, 
                       web_search_results: str, 
                       sources: List[str],
                       callback: Optional[Callable[[str], None]] = None,
                       with_details: bool = False) -> Dict[str, Any]:
        """
        Process content through the complete hallucination management pipeline.
        
        Args:
            query: Original query that prompted the content
            content: Content to process
            web_search_results: Web search results for reference
            sources: List of source URLs
            callback: Optional callback for progress updates
            with_details: If True, include detailed evaluation data in results
            
        Returns:
            Dict containing processed content and metadata
        """
        if callback:
            callback("Processing content with full hallucination management pipeline...")
        
        # Initial evaluation
        if callback:
            callback("Evaluating response for query: " + query[:50] + "...")
        
        initial_evaluation = self.hallucination_checker.evaluate_response(
            query, content, web_search_results, sources
        )
        
        initial_score = initial_evaluation.get("faithfulness_score", 0)
        problematic_claims = initial_evaluation.get("problematic_claims", [])
        
        # Verify and potentially improve the content
        verification_result = self.content_verification.verify_content(
            query=query,
            response=content,
            web_search_results=web_search_results,
            sources=sources,
            callback=callback
        )
        
        # Extract key results
        is_verified = verification_result.get("verification_passed", False)
        improved_content = verification_result.get("final_content", content)
        final_score = verification_result.get("final_score", initial_score)
        improvement_performed = verification_result.get("improvement_performed", False)
        iterations = verification_result.get("iterations", 0)
        
        # Add verification metadata if requested
        final_content = improved_content
        if is_verified and improved_content != content:
            # Only add verification metadata if content was actually improved and verified
            final_content = self.content_verification.add_verification_metadata(
                improved_content, verification_result
            )
        
        # Prepare result dictionary
        result = {
            "initial_content": content,
            "improved_content": improved_content,  # Make sure we're storing the actual improved content
            "final_content": final_content,
            "initial_score": initial_score,
            "final_score": final_score,
            "verification_passed": is_verified,
            "problematic_claims": problematic_claims,
            "iterations": iterations,
            "improved": improvement_performed
        }
        
        # Include detailed data if requested
        if with_details:
            result["initial_evaluation"] = initial_evaluation
            result["verification_result"] = verification_result
            
            # Create improvement report if available
            if hasattr(self.feedback_loop, 'generate_improvement_report') and improvement_performed:
                result["improvement_report"] = self.feedback_loop.generate_improvement_report({
                    "initial_score": initial_score,
                    "final_score": final_score,
                    "iterations": iterations,
                    "status": "Passed" if is_verified else "Failed",
                    "verification_passed": is_verified,
                    "metrics": self.feedback_loop.get_iteration_metrics()
                })
        
        return result
    
    def evaluate_only(self, 
                     query: str, 
                     content: str, 
                     web_search_results: str, 
                     sources: List[str]) -> Dict[str, Any]:
        """
        Evaluate content without attempting to improve it.
        
        Args:
            query: Original query that prompted the content
            content: Content to evaluate
            web_search_results: Web search results for reference
            sources: List of source URLs
            
        Returns:
            Dict containing evaluation results
        """
        evaluation = self.hallucination_checker.evaluate_response(
            query, content, web_search_results, sources
        )
        
        # Format response for easier consumption
        score = evaluation.get("faithfulness_score", 0)
        assessment = evaluation.get("assessment", "Unknown")
        problematic_claims = evaluation.get("problematic_claims", [])
        
        return {
            "faithfulness_score": score,
            "assessment": assessment,
            "problematic_claims": problematic_claims,
            "evaluation_details": evaluation
        }

# Usage example
def example_usage():
    # Initialize the system
    hallucination_mgmt = HallucinationManagement(level="standard")
    
    # Sample input data
    query = "Tell me about quantum computing"
    response = "Quantum computing uses qubits that can be in superposition states..."
    web_search_results = "Sources about quantum computing..."
    sources = ["https://example.com/quantum"]
    
    # Process function
    def progress_update(update):
        print(f"Progress: {update}")
    
    # Process content
    result = hallucination_mgmt.process_content(
        query, response, web_search_results, sources, progress_update, with_details=True
    )
    
    # Use the verified content
    verified_content = result["final_content"]
    print(f"Verified content (score: {result['final_score']:.2f}):")
    print(verified_content)
    
if __name__ == "__main__":
    example_usage()
