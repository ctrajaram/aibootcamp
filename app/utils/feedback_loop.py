"""
Feedback Loop module for real-time content improvement.
This module provides functionality to iteratively improve content based on hallucination detection.
"""

import os
from typing import Dict, Any, List, Optional, Callable
from openai import OpenAI
import time
from app.agents.hallucination_checker import HallucinationChecker
from app.utils.content_processor import ContentProcessor
import json

class FeedbackLoop:
    """
    A feedback loop for iteratively improving content based on hallucination detection.
    """
    
    def __init__(self, 
                hallucination_checker: Any = None, 
                content_processor: Any = None,
                max_iterations: int = 3, 
                model: str = "gpt-4o",
                target_score: float = 0.9):
        """
        Initialize the feedback loop for content improvement.
        
        Args:
            hallucination_checker: Instance of HallucinationChecker
            content_processor: Instance of ContentProcessor
            max_iterations: Maximum number of improvement iterations
            model: Model to use for evaluation and improvement
            target_score: Target faithfulness score to achieve
        """
        self.max_iterations = max_iterations
        self.model = model
        self.target_score = target_score
        self.metrics = []
        
        # Load hallucination checker if not provided
        if hallucination_checker is None:
            from app.agents.hallucination_checker import HallucinationChecker
            hallucination_checker = HallucinationChecker(model=model)
            print("Initializing HallucinationChecker...")
            
        self.hallucination_checker = hallucination_checker
        
        # Load content processor if not provided
        if content_processor is None:
            from app.utils.content_processor import ContentProcessor
            content_processor = ContentProcessor(model=model)
            print("Initializing ContentProcessor...")
            
        self.content_processor = content_processor
    
    def improve_content(self, query: str, content: str, web_search_results: str, sources: List[str], 
                       callback: Optional[Callable[[str], None]] = None) -> Dict[str, Any]:
        """
        Improve content based on hallucination detection and correction.
        
        Args:
            query: The original query that prompted the content
            content: The original content to improve
            web_search_results: Raw web search results for context
            sources: List of source URLs
            callback: Optional callback for reporting progress
            
        Returns:
            Dict with improved content and metadata
        """
        print(f"Starting content improvement feedback loop for query: {query[:50]}...")
        
        # Initialize metrics
        self.metrics = []
        
        # Cache original content for comparison
        original_content = content
        current_content = content
        
        # Get initial evaluation
        if callback:
            callback("Evaluating initial content...")
            
        initial_evaluation = self._evaluate_content(query, content, web_search_results, sources)
        initial_score = initial_evaluation.get("faithfulness_score", 0)
        
        # Record initial metrics
        self.metrics.append({
            "iteration": 0,
            "score": initial_score,
            "problematic_claims": len(initial_evaluation.get("problematic_claims", [])),
            "assessment": initial_evaluation.get("assessment", "Unknown")
        })
        
        # Check if score already meets target
        if initial_score >= self.target_score:
            return {
                "initial_content": original_content,
                "improved_content": content,
                "final_content": content,
                "initial_score": initial_score,
                "final_score": initial_score,
                "iterations": 0,
                "improved": False,
                "metrics": self.metrics,
                "verification_passed": True,
                "status": "Already met quality criteria"
            }
            
        # Begin improvement loop
        best_content = content
        best_score = initial_score
        best_evaluation = initial_evaluation
        previous_hashes = {self._generate_cache_key(content)}
        verification_passed = False
        status = "Failed to meet quality criteria"
        
        # Main improvement loop
        for iteration in range(1, self.max_iterations + 1):
            if callback:
                callback(f"Improvement iteration {iteration}/{self.max_iterations}: Current score = {best_score:.3f}")
                
            print(f"Improvement iteration {iteration}/{self.max_iterations}: Current score = {best_score:.3f}")
            
            # Get the latest evaluation
            current_evaluation = best_evaluation
            problematic_claims = current_evaluation.get("problematic_claims", [])
            
            # Break if no more issues to fix
            if not problematic_claims and best_score >= self.target_score:
                if callback:
                    callback(f"No issues found, content meets quality criteria (score={best_score:.2f})")
                verification_passed = True
                status = "Successfully improved"
                break
                
            # Debug the claims we're working with
            print(f"DEBUG: Problematic claims structure: {json.dumps(problematic_claims, indent=2)}")
            
            # Attempt to fix hallucinations
            if callback:
                callback(f"Fixing {len(problematic_claims)} problematic claims...")
                
            try:
                print("Fixing hallucinations in content...")
                improved_content = self.content_processor.fix_hallucinations(
                    query=query, 
                    content=best_content,
                    problematic_claims=problematic_claims,
                    context=web_search_results
                )
                
                # Skip evaluation if content is identical to previous version
                content_hash = self._generate_cache_key(improved_content)
                if content_hash in previous_hashes:
                    print("Minimal changes detected, trying with more aggressive rewriting...")
                    
                    # Try a more aggressive approach - full rewrite
                    improved_content = self.content_processor._rewrite_full_content(
                        query=query,
                        content=best_content,
                        context=web_search_results
                    )
                    
                    # Check if still minimal changes
                    content_hash = self._generate_cache_key(improved_content)
                    if content_hash in previous_hashes:
                        print("Still no significant improvement after aggressive rewrite, stopping iterations.")
                        break
                
                # Track this version
                previous_hashes.add(content_hash)
                
                # Evaluate the improved content
                print("Evaluating improved content...")
                improved_evaluation = self._evaluate_content(query, improved_content, web_search_results, sources)
                improved_score = improved_evaluation.get("faithfulness_score", 0)
                
                # Record metrics for this iteration
                self.metrics.append({
                    "iteration": iteration,
                    "score": improved_score,
                    "problematic_claims": len(improved_evaluation.get("problematic_claims", [])),
                    "assessment": improved_evaluation.get("assessment", "Unknown")
                })
                
                # Update best content if this improved the score
                if improved_score > best_score:
                    print(f"New best score: {improved_score:.3f} (previous: {best_score:.3f})")
                    best_content = improved_content
                    best_score = improved_score
                    best_evaluation = improved_evaluation
                    
                    # Check if we've met the target score
                    if best_score >= self.target_score:
                        verification_passed = True
                        status = "Successfully improved"
                        if callback:
                            callback(f"Target quality achieved: score={best_score:.2f}")
                        break
                else:
                    print(f"No score improvement: {improved_score:.3f} <= {best_score:.3f}")
                
                # Check for minimal improvement overall
                if iteration >= 2 and best_score <= initial_score + 0.1:
                    print(f"No significant improvement after {iteration} iterations, stopping")
                    break
                    
            except Exception as e:
                print(f"Error in improvement iteration {iteration}: {str(e)}")
                # traceback.print_exc()
                continue
        
        # Generate final result
        improvement_delta = best_score - initial_score
        meaningful_improvement = improvement_delta > 0.05
        
        final_status = status
        if meaningful_improvement:
            final_status = "Successfully improved" if verification_passed else "Improved but not verified"
        else:
            final_status = "No meaningful improvement"
            
        result = {
            "initial_content": original_content,
            "improved_content": best_content,
            "final_content": best_content,
            "initial_score": initial_score,
            "final_score": best_score,
            "initial_evaluation": initial_evaluation,
            "final_evaluation": best_evaluation,
            "verification_passed": verification_passed,
            "iterations": iteration if iteration < self.max_iterations else self.max_iterations,
            "improved": meaningful_improvement,
            "metrics": self.metrics,
            "status": final_status,
            "improvement_delta": improvement_delta
        }
        
        if callback:
            callback(f"Improvement complete: initial={initial_score:.2f}, final={best_score:.2f}")
            
        print(f"Improvement complete: initial={initial_score:.2f}, final={best_score:.2f}")
        
        return result
    
    def _content_similarity(self, content1: str, content2: str) -> float:
        """
        Calculate similarity between two content strings.
        
        Args:
            content1: First content string
            content2: Second content string
            
        Returns:
            Similarity score between 0 and 1
        """
        # Implement similarity check with sequence matcher
        from difflib import SequenceMatcher
        return SequenceMatcher(None, content1, content2).ratio()
    
    def _generate_cache_key(self, content: str) -> str:
        """
        Generate a cache key for content to avoid redundant evaluations.
        
        Args:
            content: The content to generate a key for
            
        Returns:
            Cache key as string
        """
        # Create a deterministic hash for the content
        import hashlib
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def _evaluate_content(self, query: str, content: str, web_search_results: str, sources: List[str]) -> Dict[str, Any]:
        """
        Evaluate content for hallucinations, with caching for efficiency.
        
        Args:
            query: The original query
            content: The content to evaluate
            web_search_results: Web search results for grounding
            sources: List of source URLs
            
        Returns:
            Evaluation results
        """
        # Generate a cache key for this content
        cache_key = self._generate_cache_key(content)
        
        # Check if we've already evaluated similar content
        if hasattr(self, '_evaluation_cache') and cache_key in self._evaluation_cache:
            print("Using cached evaluation result")
            return self._evaluation_cache[cache_key]
        
        print("Evaluating response for query: " + query[:50] + "...")
        
        # Perform the evaluation
        evaluation = self.hallucination_checker.evaluate_response(
            query=query,
            response=content,
            web_search_results=web_search_results,
            sources=sources
        )
        
        # Initialize the cache if it doesn't exist
        if not hasattr(self, '_evaluation_cache'):
            self._evaluation_cache = {}
            
        # Cache the result
        self._evaluation_cache[cache_key] = evaluation
        
        return evaluation
    
    def get_iteration_metrics(self) -> List[Dict[str, Any]]:
        """
        Get metrics for each improvement iteration.
        
        Returns:
            List of metric dictionaries
        """
        return self.metrics
    
    def generate_improvement_report(self, results: Dict[str, Any]) -> str:
        """
        Generate a human-readable report of the improvement process.
        
        Args:
            results: Results from the improve_content method
            
        Returns:
            Formatted report string
        """
        report_lines = [
            "## Content Improvement Report",
            "",
            f"- **Initial Faithfulness Score**: {results['initial_score']:.2f}",
            f"- **Final Faithfulness Score**: {results['final_score']:.2f}",
            f"- **Improvement**: {(results['final_score'] - results['initial_score']):.2f} points",
            f"- **Iterations Required**: {results['iterations']}",
            f"- **Verification Status**: {results['status']}",
            "",
            "### Iteration Metrics",
            ""
        ]
        
        # Add metrics for each iteration
        for metric in results.get('metrics', []):
            report_lines.append(
                f"- Iteration {metric['iteration']}: Score = {metric['score']:.2f}, "
                f"Issues = {metric['problematic_claims']}, "
                f"Assessment = {metric['assessment']}"
            )
            
        # Add conclusion
        report_lines.extend([
            "",
            "### Conclusion",
            "",
            "The content " + (
                "successfully passed verification checks." if results['verification_passed'] 
                else "did not meet the minimum quality threshold."
            )
        ])
        
        return "\n".join(report_lines)
