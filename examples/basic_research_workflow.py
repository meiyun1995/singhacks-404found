"""
Example: Basic research workflow
Demonstrates how to use the multi-agent system for a research task.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from workflow_orchestrator import WorkflowOrchestrator
from utils import save_to_json
from rich.console import Console


def main():
    """Run a basic research workflow example."""
    console = Console()
    
    console.print("\n[bold blue]Multi-Agent Research Workflow Example[/bold blue]\n")
    
    # Initialize orchestrator
    try:
        orchestrator = WorkflowOrchestrator()
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        console.print("[yellow]Make sure to set OPENAI_API_KEY in your .env file[/yellow]")
        return
    
    # Define research topic
    topic = "The impact of artificial intelligence on modern healthcare"
    
    # Run the workflow
    try:
        results = orchestrator.run_research_workflow(topic)
        
        # Display results
        console.print("\n[bold green]Results:[/bold green]\n")
        
        console.print("[cyan]Research:[/cyan]")
        console.print(f"{results['research'][:300]}...\n")
        
        console.print("[cyan]Written Content:[/cyan]")
        console.print(f"{results['written_content'][:300]}...\n")
        
        console.print("[cyan]Review:[/cyan]")
        console.print(f"{results['review'][:300]}...\n")
        
        # Save results
        filepath = save_to_json(results, "research_workflow_results")
        console.print(f"\n[green]Full results saved to: {filepath}[/green]")
        
    except Exception as e:
        console.print(f"[red]Error during workflow execution: {e}[/red]")
        raise


if __name__ == "__main__":
    main()
