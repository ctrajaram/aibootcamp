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
    
    def process_content(self, query: str, content: str, web_search_results: str, sources: List[str], 
                        callback: Optional[Callable[[str], None]] = None) -> Dict[str, Any]:
        """
        Process content through hallucination management pipeline.
        
        Args:
            query: The original query
            content: Content to process
            web_search_results: Web search results for context
            sources: List of source URLs
            callback: Optional callback for progress updates
            
        Returns:
            Dictionary with processed content and metadata
        """
        if callback:
            callback("Processing content with full hallucination management pipeline...")
            
        print("Processing content with full hallucination management pipeline...")
        
        # Verify content against sources
        verification_result = self.content_verification.verify_content(
            query=query,
            response=content,
            web_search_results=web_search_results,
            sources=sources,
            callback=callback
        )
        
        # Format the verification results for UI display
        hallucination_metrics = self.format_verification_results(verification_result)
        
        # Add verification badge to content if it was improved
        improved_content = verification_result["final_content"]
        
        if verification_result["verification_passed"]:
            score = round(verification_result["final_score"], 2)
            improved_content += f"\n\n---\n*Content [VERIFIED] ({score*100}% factual accuracy)"
            
            if verification_result["improvement_performed"]:
                improved_content += " [Auto-improved]*"
            else:
                improved_content += "*"
        
        # Return the result with all metadata
        result = {
            "original_content": content,
            "processed_content": improved_content,
            "verification_passed": verification_result["verification_passed"],
            "verification_result": verification_result,
            "hallucination_metrics": hallucination_metrics
        }
        
        return result
    
    def format_verification_results(self, verification_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format verification results for display in the UI.
        
        Args:
            verification_result: The verification result dictionary
            
        Returns:
            Formatted metrics suitable for UI display
        """
        initial_score = verification_result.get("initial_score", 0)
        final_score = verification_result.get("final_score", 0)
        improvement = 0
        
        if initial_score > 0:
            improvement = ((final_score - initial_score) / initial_score) * 100
        elif final_score > 0:
            improvement = 100
            
        # Format metrics for UI display
        score_color = "red"
        if final_score >= 0.9:
            score_color = "green"
        elif final_score >= 0.7:
            score_color = "orange"
        
        # Prepare hallucination metrics for UI
        metrics = {
            "summary": {
                "initial_score": round(initial_score, 2),
                "final_score": round(final_score, 2),
                "improvement": round(improvement, 1),
                "score_color": score_color,
                "iterations": verification_result.get("iterations", 0),
                "status": verification_result.get("status", "Unknown"),
                "verification_passed": verification_result.get("verification_passed", False)
            },
            "detailed_metrics": verification_result.get("metrics", []),
            "problematic_claims": verification_result.get("final_evaluation", {}).get("problematic_claims", [])
        }
        
        # Add a simple HTML representation for easy UI integration
        html_representation = f"""
        <div class="hallucination-metrics">
            <h3>Content Verification Results</h3>
            <div class="metrics-summary">
                <div class="metric">
                    <span class="label">Initial Score:</span>
                    <span class="value">{metrics['summary']['initial_score']:.2f}</span>
                </div>
                <div class="metric">
                    <span class="label">Final Score:</span>
                    <span class="value" style="color: {score_color};">{metrics['summary']['final_score']:.2f}</span>
                </div>
                <div class="metric">
                    <span class="label">Improvement:</span>
                    <span class="value">{metrics['summary']['improvement']:.1f}%</span>
                </div>
                <div class="metric">
                    <span class="label">Status:</span>
                    <span class="value">{metrics['summary']['status']}</span>
                </div>
            </div>
        """
        
        # Add problematic claims section if any exist
        if metrics['problematic_claims']:
            html_representation += """
            <div class="problematic-claims">
                <h4>Detected Issues:</h4>
                <ul>
            """
            
            for claim in metrics['problematic_claims'][:5]:  # Show top 5 claims
                html_representation += f"""
                <li>
                    <div class="claim">{claim.get('text', '')}</div>
                    <div class="correction"><strong>Correction:</strong> {claim.get('correction', 'No correction available')}</div>
                </li>
                """
                
            html_representation += """
                </ul>
            </div>
            """
            
        html_representation += "</div>"
        metrics['html'] = html_representation
        
        return metrics
    
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
        query, response, web_search_results, sources, progress_update
    )
    
    # Use the verified content
    verified_content = result["processed_content"]
    print(f"Verified content (score: {result['verification_result']['final_score']:.2f}):")
    print(verified_content)
    
if __name__ == "__main__":
    example_usage()
