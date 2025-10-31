"""
Example: Custom workflow
Demonstrates how to create a custom multi-agent workflow.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from workflow_orchestrator import WorkflowOrchestrator
from utils import save_to_json
from rich.console import Console


def main():
    """Run a custom workflow example."""
    console = Console()
    
    console.print("\n[bold blue]Custom Multi-Agent Workflow Example[/bold blue]\n")
    
    # Initialize orchestrator
    try:
        orchestrator = WorkflowOrchestrator()
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        console.print("[yellow]Make sure to set OPENAI_API_KEY in your .env file[/yellow]")
        return
    
    # Define custom workflow
    task_description = "Create a blog post about sustainable energy"
    
    steps = [
        {
            "agent": "coordinator",
            "action": "plan_workflow",
            "params": {
                "task_description": task_description,
            },
        },
        {
            "agent": "researcher",
            "action": "research_topic",
            "params": {
                "topic": "sustainable energy solutions",
                "depth": "moderate",
            },
        },
        {
            "agent": "writer",
            "action": "write_content",
            "params": {
                "content_type": "blog post",
                "topic": "sustainable energy",
            },
        },
        {
            "agent": "reviewer",
            "action": "review_content",
            "params": {
                "content": "Generated content",  # In practice, this would use results from previous step
                "criteria": ["clarity", "engagement", "accuracy"],
            },
        },
    ]
    
    # Run the workflow
    try:
        results = orchestrator.run_custom_workflow(task_description, steps)
        
        # Display results
        console.print("\n[bold green]Workflow Results:[/bold green]\n")
        for step_name, result in results.items():
            console.print(f"[cyan]{step_name}:[/cyan]")
            console.print(f"{str(result)[:200]}...\n")
        
        # Save results
        filepath = save_to_json(results, "custom_workflow_results")
        console.print(f"\n[green]Full results saved to: {filepath}[/green]")
        
    except Exception as e:
        console.print(f"[red]Error during workflow execution: {e}[/red]")
        raise


if __name__ == "__main__":
    main()
