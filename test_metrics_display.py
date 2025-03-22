"""
Test script demonstrating how to display hallucination metrics in a user interface.
This script shows how to:
1. Process content through the hallucination management system
2. Extract the metrics for display
3. Generate an HTML file with the verification results
"""

import os
import json
import webbrowser
from pathlib import Path
from openai import OpenAI
from app.utils.hallucination_management import HallucinationManagement

# Ensure the OpenAI API key is set
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY environment variable must be set")

def save_metrics_to_html(metrics_data, output_path="ui_example/result.html"):
    """Save hallucination metrics to an HTML file for display"""
    
    # Create the output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Read the template HTML file
    template_path = Path("ui_example/hallucination_metrics.html")
    with open(template_path, "r", encoding="utf-8") as f:
        template_html = f.read()
    
    # Convert the metrics data to JSON for the JavaScript to use
    metrics_json = json.dumps(metrics_data)
    
    # Replace the sample data in the template with our actual data
    # This is a simple replacement; in a real app you might use a proper templating engine
    modified_html = template_html.replace(
        "const sampleData = {",
        f"const sampleData = {metrics_json};"
    ).replace(
        "};",
        ""
    )
    
    # Write the modified HTML to the output file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(modified_html)
    
    return output_path

def main():
    print("=== HALLUCINATION METRICS DISPLAY DEMO ===\n")
    
    # Sample content with hallucinations (same as in the test_hallucination_management.py)
    query = "Explain the difference between Docker and virtual machines"
    content_with_hallucinations = """
Docker and virtual machines (VMs) are both technologies used for containerization and virtualization.

Docker was invented by Solomon Hykes in 2010 at dotCloud, a PaaS company. Docker containers are much more lightweight because they share the host OS kernel and don't need a full operating system for each container. Docker containers typically start in microseconds, while VMs can take minutes.

Virtual machines were first developed by IBM in 1972 as a way to partition mainframe computers. Each VM includes a full operating system with its own kernel, which leads to greater isolation but higher resource usage. VMs require a hypervisor like VMware ESXi or Microsoft's Hyper-V Division.

Docker containers are not secure for multi-tenant environments because they can access the full Linux kernel memory, while VMs provide complete isolation with memory protection. Docker also uses patented "BiTreeFS" technology for its filesystem which improves efficiency by 75% over traditional filesystems.

When choosing between Docker and VMs, Docker is always faster and more resource-efficient, but VMs provide better compatibility with legacy software like COBOL applications.
"""
    
    # Sample web search results (simplified for demonstration)
    web_search_results = """
Docker was created by Solomon Hykes in 2013 and released as open-source software. It's designed to make it easier to create, deploy, and run applications by using containers.

Virtual machines use hypervisors like VMware ESXi, Microsoft Hyper-V, or KVM to create and run virtual machines. Each VM runs its own operating system and applications.

Containers share the host system's kernel but can run isolated processes. Docker uses namespaces and cgroups to isolate containers.

Docker uses an overlay filesystem and is generally more resource-efficient than VMs for many workloads.
"""
    
    # Sample sources
    sources = [
        "https://www.docker.com/what-container",
        "https://www.vmware.com/topics/glossary/content/virtual-machine",
        "https://opensource.com/resources/virtualization"
    ]
    
    # Initialize the hallucination management system
    print("Initializing hallucination management system...")
    hallucination_mgmt = HallucinationManagement(level="standard")
    
    # Process the content
    print("Processing content to detect and fix hallucinations...")
    result = hallucination_mgmt.process_content(
        query=query,
        content=content_with_hallucinations,
        web_search_results=web_search_results,
        sources=sources
    )
    
    # Extract metrics data for UI display
    metrics_data = {
        "original_content": content_with_hallucinations,
        "processed_content": result["processed_content"],
        "hallucination_metrics": result["hallucination_metrics"]
    }
    
    # Create an HTML file with the results
    print("Generating visualization of hallucination metrics...")
    output_file = save_metrics_to_html(metrics_data)
    
    # Open the file in a web browser
    print(f"Opening {output_file} in your web browser...")
    webbrowser.open(f"file://{os.path.abspath(output_file)}")
    
    print("\nMetrics Summary:")
    print(f"- Initial faithfulness score: {result['hallucination_metrics']['summary']['initial_score']:.2f}")
    print(f"- Final faithfulness score: {result['hallucination_metrics']['summary']['final_score']:.2f}")
    print(f"- Improvement: {result['hallucination_metrics']['summary']['improvement']:.1f}%")
    print(f"- Status: {result['hallucination_metrics']['summary']['status']}")
    
    print("\nDemo complete! The visualization is now open in your browser.")

if __name__ == "__main__":
    main()
