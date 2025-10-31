"""
Main entry point for the multi-agent workflow system.
"""
import argparse
import json
import sys
from rich.console import Console

from workflow_orchestrator import WorkflowOrchestrator
from agents import ResearchAgent, WriterAgent, ReviewerAgent
from utils import save_to_json, validate_environment
from config import AgentConfig
from openai import OpenAI


def run_interactive_mode():
    """Run the system in interactive mode."""
    console = Console()
    console.print("\n[bold blue]Multi-Agent Workflow System - Interactive Mode[/bold blue]\n")
    
    try:
        validate_environment()
        orchestrator = WorkflowOrchestrator()
        
        console.print("Available workflows:")
        console.print("1. Research Workflow (research → write → review)")
        console.print("2. Quick Research (research only)")
        console.print("3. Content Creation (write → review)")
        
        choice = console.input("\n[cyan]Select workflow (1-3): [/cyan]")
        
        # Create shared client and config for consistency
        config = AgentConfig()
        client = OpenAI(api_key=config.OPENAI_API_KEY)
        
        if choice == "1":
            topic = console.input("[cyan]Enter research topic: [/cyan]")
            results = orchestrator.run_research_workflow(topic)
            filepath = save_to_json(results, "research_workflow")
            console.print(f"\n[green]Results saved to: {filepath}[/green]")
            
        elif choice == "2":
            topic = console.input("[cyan]Enter research topic: [/cyan]")
            researcher = ResearchAgent(client=client, config=config)
            result = researcher.research_topic(topic)
            console.print(f"\n[green]Research Result:[/green]\n{result}")
            
        elif choice == "3":
            topic = console.input("[cyan]Enter content topic: [/cyan]")
            content_type = console.input("[cyan]Content type (article/blog/report): [/cyan]")
            
            writer = WriterAgent(client=client, config=config)
            content = writer.write_content(content_type, topic)
            
            reviewer = ReviewerAgent(client=client, config=config)
            review = reviewer.review_content(content)
            
            results = {"content": content, "review": review}
            filepath = save_to_json(results, "content_creation")
            console.print(f"\n[green]Results saved to: {filepath}[/green]")
            
        else:
            console.print("[yellow]Invalid choice[/yellow]")
            
    except ValueError as e:
        console.print(f"[red]Configuration Error: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Multi-Agent Workflow System using OpenAI"
    )
    parser.add_argument(
        "--mode",
        choices=["interactive", "research", "custom"],
        default="interactive",
        help="Execution mode"
    )
    parser.add_argument(
        "--topic",
        type=str,
        help="Topic for research workflow"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output file path"
    )
    
    args = parser.parse_args()
    
    console = Console()
    
    try:
        validate_environment()
        
        if args.mode == "interactive":
            run_interactive_mode()
            
        elif args.mode == "research":
            if not args.topic:
                console.print("[red]Error: --topic required for research mode[/red]")
                sys.exit(1)
            
            orchestrator = WorkflowOrchestrator()
            results = orchestrator.run_research_workflow(args.topic)
            
            if args.output:
                filepath = args.output
                with open(filepath, "w") as f:
                    json.dump(results, f, indent=2)
            else:
                filepath = save_to_json(results, "research_workflow")
            
            console.print(f"\n[green]Results saved to: {filepath}[/green]")
            
        elif args.mode == "custom":
            console.print("[yellow]Custom mode: Please use the WorkflowOrchestrator API directly[/yellow]")
            console.print("See examples/custom_workflow.py for reference")
            
    except ValueError as e:
        console.print(f"[red]Configuration Error: {e}[/red]")
        console.print("[yellow]Please ensure OPENAI_API_KEY is set in .env file[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
