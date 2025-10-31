"""
Example: Individual agent usage
Demonstrates how to use individual agents directly.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents import ResearchAgent, WriterAgent, ReviewerAgent
from rich.console import Console


def main():
    """Run individual agent examples."""
    console = Console()
    
    console.print("\n[bold blue]Individual Agent Usage Examples[/bold blue]\n")
    
    try:
        # Research Agent Example
        console.print("[bold cyan]1. Research Agent Example[/bold cyan]\n")
        researcher = ResearchAgent()
        research_result = researcher.research_topic(
            topic="Machine learning in finance",
            depth="brief"
        )
        console.print(f"[green]Research Result:[/green]\n{research_result[:300]}...\n\n")
        
        # Writer Agent Example
        console.print("[bold cyan]2. Writer Agent Example[/bold cyan]\n")
        writer = WriterAgent()
        article = writer.write_content(
            content_type="summary",
            topic="The future of renewable energy"
        )
        console.print(f"[green]Written Content:[/green]\n{article[:300]}...\n\n")
        
        # Reviewer Agent Example
        console.print("[bold cyan]3. Reviewer Agent Example[/bold cyan]\n")
        reviewer = ReviewerAgent()
        review = reviewer.review_content(
            content=article,
            criteria=["clarity", "coherence", "engagement"]
        )
        console.print(f"[green]Review Feedback:[/green]\n{review[:300]}...\n\n")
        
        console.print("[bold green]All agent examples completed successfully![/bold green]")
        
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        console.print("[yellow]Make sure to set OPENAI_API_KEY in your .env file[/yellow]")
    except Exception as e:
        console.print(f"[red]Error during execution: {e}[/red]")
        raise


if __name__ == "__main__":
    main()
