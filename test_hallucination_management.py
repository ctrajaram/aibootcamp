"""
Test script for the Hallucination Management System
This script demonstrates how the system detects and fixes hallucinations.
"""

import os
import sys
import time
import json
from dotenv import load_dotenv
from typing import List, Dict, Any, Callable

# Load environment variables
load_dotenv()

# Add app directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import hallucination management components
from app.utils.hallucination_management import HallucinationManagement

def test_with_real_hallucination():
    """Test hallucination management with real-world hallucinations"""
    print("\n=== TESTING WITH REAL HALLUCINATIONS ===\n")
    
    # Sample query and response with known hallucinations
    query = "Explain the difference between Docker and virtual machines"
    
    # Response with deliberately inserted hallucinations:
    # - "BiTreeFS" technology (fictional)
    # - "Hyper-V Division" (incorrectly named)
    # - Docker always faster (oversimplification)
    # - Docker containers start in microseconds (exaggeration)
    # - IBM in 1972 for VMs (incorrect date)
    response_with_hallucination = """
Docker and virtual machines (VMs) are both technologies used for containerization and virtualization.

Docker was invented by Solomon Hykes in 2010 at dotCloud, a PaaS company. Docker containers are much more lightweight because they share the host OS kernel and don't need a full operating system for each container. Docker containers typically start in microseconds, while VMs can take minutes.

Virtual machines were first developed by IBM in 1972 as a way to partition mainframe computers. Each VM includes a full operating system with its own kernel, which leads to greater isolation but higher resource usage. VMs require a hypervisor like VMware ESXi or Microsoft's Hyper-V Division.

Docker containers are not secure for multi-tenant environments because they can access the full Linux kernel memory, while VMs provide complete isolation with memory protection. Docker also uses patented "BiTreeFS" technology for its filesystem which improves efficiency by 75% over traditional filesystems.

When choosing between Docker and VMs, Docker is always faster and more resource-efficient, but VMs provide better compatibility with legacy software like COBOL applications.
"""
    
    # Sample web search results with correct information
    web_search_results = """
Docker was created by Solomon Hykes in 2013 and released as open-source software. Docker containers share the host system's kernel and isolate application processes from each other. Containers are much more lightweight than VMs because they don't require a full OS for each instance.

Virtual machines were pioneered by IBM in the 1960s and became widely used by the 1970s. Each VM runs a complete operating system with its own kernel on top of a hypervisor like VMware ESXi, Microsoft Hyper-V, or KVM.

Docker containers start in seconds (not microseconds), while VMs typically take minutes to boot. Docker uses overlay filesystem technology which is efficient but not called "BiTreeFS".

Containers have less isolation than VMs because they share the host kernel, making them potentially less secure for multi-tenant environments. However, Docker has added security features like namespaces and cgroups to improve isolation.

Docker is generally more resource-efficient than VMs for many workloads, but not always faster for all use cases. VMs can provide better performance for certain workloads, especially those that benefit from direct hardware access.
"""
    
    # Sample sources
    sources = [
        "https://www.docker.com/resources/what-container/",
        "https://www.vmware.com/topics/glossary/content/virtual-machine",
        "https://docs.microsoft.com/en-us/virtualization/hyper-v-on-windows/about/"
    ]
    
    # Define a progress callback
    def progress_callback(message: str):
        print(message)
    
    # Initialize HallucinationManagement with standard level
    management = HallucinationManagement(level="standard")
    
    # Display original response
    print("Original response (with hallucinations):")
    print("-" * 80)
    print(response_with_hallucination)
    print("-" * 80)
    
    print("\nProcessing content through hallucination management system...")
    
    # Process content through the hallucination management pipeline
    start_time = time.time()
    
    result = management.process_content(
        query=query,
        content=response_with_hallucination,
        web_search_results=web_search_results,
        sources=sources,
        callback=progress_callback,
        with_details=True
    )
    
    processing_time = time.time() - start_time
    
    # Display improved content
    print("\nProcessed response (hallucinations fixed):")
    print("-" * 80)
    print(result["final_content"])
    print("-" * 80)
    
    # Display improvement metrics
    print("\nSummary:")
    print(f"- Initial faithfulness score: {result['initial_score']:.2f}")
    print(f"- Final faithfulness score: {result['final_score']:.2f}")
    print(f"- Improvement: {(result['final_score'] - result['initial_score']) * 100:.1f}%")
    print(f"- Iterations required: {result.get('iterations', 0)}")
    
    # Display detailed hallucination analysis
    print("\nDetected hallucinations in original response:")
    
    for i, claim in enumerate(result.get('problematic_claims', [])):
        print(f"\n{i+1}. \"{claim['text']}\"")
        print(f"   Issue: {claim['reason']}")
        if 'correction' in claim:
            print(f"   Correction: {claim['correction']}")
    
    # Display report if available
    if 'improvement_report' in result:
        print("\nDetailed Improvement Report:")
        print(result['improvement_report'])
    
    print("\nTest complete!")

def test_with_multiple_hallucination_types():
    """Test hallucination management with diverse types of hallucinations"""
    print("\n=== TESTING WITH MULTIPLE HALLUCINATION TYPES ===\n")
    
    # Create different types of hallucinations to test the system's capabilities
    query = "Explain how AI models work and their limitations"
    
    response_with_diverse_hallucinations = """
AI models like GPT-4 and DALL-E 3 work by using complex neural networks that simulate human brain patterns. 

GPT-4 has exactly 1.75 trillion parameters, making it the largest language model ever created. It was trained on data from the entire internet up to April 2023, including all academic journals and books ever published. The training cost for GPT-4 was precisely $43.7 million.

All large language models (LLMs) today achieve perfect understanding of context by storing memories of previous interactions in quantum memory units. This allows them to achieve 100% accuracy on all mathematical problems.

According to MIT's AI department, neural networks work by creating digital "neurons" that perfectly replicate human brain cells in all aspects. This biological similarity enables their reasoning capabilities.

The main limitation of LLMs is the "combinatorial explosive barrier" - a mathematical theorem proven by Alan Turing in 1952 that shows all neural networks will eventually reach perfect accuracy but are limited by hardware constraints.
"""
    
    # Sample web search results with correct information
    web_search_results = """
AI models such as GPT-4 and DALL-E use neural network architectures that are inspired by, but do not directly simulate, biological neural networks. These models consist of layers of mathematical operations with learned parameters.

GPT-4's exact parameter count has not been publicly disclosed by OpenAI, though estimates suggest it may have hundreds of billions to potentially over a trillion parameters. Training costs are also not publicly disclosed, but industry experts estimate high-end AI model training can cost millions of dollars.

Large language models do not have perfect memory of previous interactions; they typically have a limited context window. They can struggle with long-term consistency and do not achieve 100% accuracy on mathematical problems - in fact, arithmetic reasoning remains a challenge for many LLMs.

Neural networks are mathematical models comprised of weighted connections between artificial neurons, which are mathematical functions rather than biological simulations. The term "neuron" is an analogy that describes the high-level inspiration, not a literal replication.

Limitations of LLMs include:
- Contextual understanding limitations
- Inability to reason perfectly about the world
- Lack of grounding in physical reality
- Tendency to generate plausible-sounding but incorrect information
- Limited ability to update knowledge without retraining
- Sensitivity to input phrasing
- Difficulty with certain types of logical and mathematical reasoning
"""
    
    # Sample sources
    sources = [
        "https://openai.com/research/gpt-4",
        "https://ai.stanford.edu/blog/understanding-neural-networks/",
        "https://www.nature.com/articles/s41598-022-17452-0"
    ]
    
    # Define a progress callback
    def progress_callback(message: str):
        print(message)
    
    # Initialize HallucinationManagement with high level
    management = HallucinationManagement(level="high")
    
    # Display original response
    print("Original response (with diverse hallucinations):")
    print("-" * 80)
    print(response_with_diverse_hallucinations)
    print("-" * 80)
    
    print("\nProcessing content through hallucination management system...")
    
    # Process content through the hallucination management pipeline
    start_time = time.time()
    
    result = management.process_content(
        query=query,
        content=response_with_diverse_hallucinations,
        web_search_results=web_search_results,
        sources=sources,
        callback=progress_callback,
        with_details=True
    )
    
    processing_time = time.time() - start_time
    
    # Display improved content
    print("\nProcessed response (hallucinations fixed):")
    print("-" * 80)
    print(result["final_content"])
    print("-" * 80)
    
    # Display improvement metrics
    print("\nSummary:")
    print(f"- Initial faithfulness score: {result['initial_score']:.2f}")
    print(f"- Final faithfulness score: {result['final_score']:.2f}")
    print(f"- Improvement: {(result['final_score'] - result['initial_score']) * 100:.1f}%")
    print(f"- Iterations required: {result.get('iterations', 0)}")
    
    # Display detailed hallucination analysis if available
    print("\nDetected hallucinations in original response:")
    
    for i, claim in enumerate(result.get('problematic_claims', [])):
        print(f"\n{i+1}. \"{claim['text']}\"")
        print(f"   Issue: {claim['reason']}")
        if 'correction' in claim:
            print(f"   Correction: {claim['correction']}")
    
    print("\nTest complete!")

# Main execution
if __name__ == "__main__":
    try:
        test_with_real_hallucination()
        # Uncomment to run multiple tests
        # test_with_multiple_hallucination_types()
    except Exception as e:
        print(f"Error running test: {str(e)}")
