"""
Workflow orchestrator for coordinating multiple agents.
"""
from typing import Dict, Any, Optional, List
from openai import OpenAI
from agents import (
    ResearchAgent,
    WriterAgent,
    ReviewerAgent,
    CoordinatorAgent,
)
from config import AgentConfig
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn


class WorkflowOrchestrator:
    """Orchestrates multi-agent workflows."""
    
    def __init__(self, config: Optional[AgentConfig] = None):
        """
        Initialize the workflow orchestrator.
        
        Args:
            config: Optional configuration object
        """
        self.config = config or AgentConfig()
        self.config.validate()
        
        self.client = OpenAI(api_key=self.config.OPENAI_API_KEY)
        self.console = Console()
        
        # Initialize agents
        self.agents = {
            "researcher": ResearchAgent(client=self.client, config=self.config),
            "writer": WriterAgent(client=self.client, config=self.config),
            "reviewer": ReviewerAgent(client=self.client, config=self.config),
            "coordinator": CoordinatorAgent(client=self.client, config=self.config),
        }
        
        self.workflow_state: Dict[str, Any] = {}
        self.results: Dict[str, Any] = {}
    
    def display_step(self, step_name: str, agent_name: str, message: str = "") -> None:
        """Display a workflow step in a formatted way."""
        title = f"[bold cyan]{step_name}[/bold cyan] - [yellow]{agent_name}[/yellow]"
        self.console.print(Panel(message or f"Executing with {agent_name}", title=title))
    
    def run_research_workflow(self, topic: str) -> Dict[str, Any]:
        """
        Run a complete research-write-review workflow.
        
        Args:
            topic: The topic to research and write about
            
        Returns:
            Dictionary containing all workflow results
        """
        self.console.print(f"\n[bold green]Starting Research Workflow[/bold green]\n")
        self.console.print(f"Topic: [italic]{topic}[/italic]\n")
        
        results = {}
        
        # Step 1: Research
        self.display_step("Step 1: Research", "Research Agent")
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            task = progress.add_task("Researching topic...", total=None)
            research_result = self.agents["researcher"].research_topic(topic)
            progress.update(task, completed=True)
        
        results["research"] = research_result
        self.console.print(f"\n[dim]Research completed ({len(research_result)} chars)[/dim]\n")
        
        # Step 2: Write
        self.display_step("Step 2: Write Content", "Writer Agent")
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            task = progress.add_task("Writing content...", total=None)
            written_content = self.agents["writer"].write_content(
                content_type="article",
                topic=topic,
                research_data=research_result,
            )
            progress.update(task, completed=True)
        
        results["written_content"] = written_content
        self.console.print(f"\n[dim]Content written ({len(written_content)} chars)[/dim]\n")
        
        # Step 3: Review
        self.display_step("Step 3: Review", "Reviewer Agent")
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            task = progress.add_task("Reviewing content...", total=None)
            review_feedback = self.agents["reviewer"].review_content(written_content)
            progress.update(task, completed=True)
        
        results["review"] = review_feedback
        self.console.print(f"\n[dim]Review completed[/dim]\n")
        
        # Summary
        self.console.print(Panel(
            "[bold green]Workflow completed successfully![/bold green]",
            title="Summary"
        ))
        
        self.results = results
        return results
    
    def run_custom_workflow(
        self,
        task_description: str,
        steps: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Run a custom workflow with specified steps.
        
        Args:
            task_description: Description of the overall task
            steps: List of step dictionaries with 'agent' and 'action' keys
            
        Returns:
            Dictionary containing all workflow results
        """
        self.console.print(f"\n[bold green]Starting Custom Workflow[/bold green]\n")
        self.console.print(f"Task: [italic]{task_description}[/italic]\n")
        
        results = {}
        
        for i, step in enumerate(steps, 1):
            agent_name = step["agent"]
            action = step["action"]
            params = step.get("params", {})
            
            if agent_name not in self.agents:
                raise ValueError(f"Unknown agent: {agent_name}")
            
            agent = self.agents[agent_name]
            self.display_step(f"Step {i}", agent.name)
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
            ) as progress:
                task = progress.add_task(f"Executing {action}...", total=None)
                
                # Execute the action
                if hasattr(agent, action):
                    result = getattr(agent, action)(**params)
                else:
                    # Fallback to generic execute
                    result = agent.execute(params.get("task", action))
                
                progress.update(task, completed=True)
            
            results[f"step_{i}_{action}"] = result
            self.console.print(f"\n[dim]Step {i} completed[/dim]\n")
        
        self.console.print(Panel(
            "[bold green]Custom workflow completed![/bold green]",
            title="Summary"
        ))
        
        self.results = results
        return results
    
    def get_results(self) -> Dict[str, Any]:
        """Get the results of the last workflow execution."""
        return self.results
    
    def save_results(self, filepath: str) -> None:
        """
        Save workflow results to a file.
        
        Args:
            filepath: Path to save the results
        """
        import json
        
        with open(filepath, "w") as f:
            json.dump(self.results, f, indent=2)
        
        self.console.print(f"[green]Results saved to {filepath}[/green]")
