"""
Specialized agent implementations.
"""
from typing import Optional, Dict, Any
from openai import OpenAI
from .base_agent import BaseAgent
from config import AgentConfig


class ResearchAgent(BaseAgent):
    """Agent specialized in research and information gathering."""
    
    def __init__(
        self,
        client: Optional[OpenAI] = None,
        config: Optional[AgentConfig] = None,
    ):
        super().__init__(role="researcher", client=client, config=config)
    
    def research_topic(self, topic: str, depth: str = "comprehensive") -> str:
        """
        Research a specific topic.
        
        Args:
            topic: The topic to research
            depth: Level of depth ('brief', 'moderate', 'comprehensive')
            
        Returns:
            Research findings
        """
        task = f"Research the following topic with {depth} depth: {topic}"
        return self.execute(task)


class WriterAgent(BaseAgent):
    """Agent specialized in content creation."""
    
    def __init__(
        self,
        client: Optional[OpenAI] = None,
        config: Optional[AgentConfig] = None,
    ):
        super().__init__(role="writer", client=client, config=config)
    
    def write_content(
        self,
        content_type: str,
        topic: str,
        research_data: Optional[str] = None,
    ) -> str:
        """
        Write content based on topic and research.
        
        Args:
            content_type: Type of content (e.g., 'article', 'blog post', 'report')
            topic: The topic to write about
            research_data: Optional research data to base content on
            
        Returns:
            Written content
        """
        task = f"Write a {content_type} about: {topic}"
        context = {"research_data": research_data} if research_data else None
        return self.execute(task, context=context)


class ReviewerAgent(BaseAgent):
    """Agent specialized in content review and quality assurance."""
    
    def __init__(
        self,
        client: Optional[OpenAI] = None,
        config: Optional[AgentConfig] = None,
    ):
        super().__init__(role="reviewer", client=client, config=config)
    
    def review_content(
        self,
        content: str,
        criteria: Optional[list] = None,
    ) -> str:
        """
        Review content and provide feedback.
        
        Args:
            content: The content to review
            criteria: Optional list of specific criteria to evaluate
            
        Returns:
            Review feedback
        """
        criteria_str = ", ".join(criteria) if criteria else "accuracy, clarity, and quality"
        task = (
            f"Review the following content based on {criteria_str}:\n\n"
            f"{content}\n\n"
            f"Provide constructive feedback and suggestions for improvement."
        )
        return self.execute(task)


class CoordinatorAgent(BaseAgent):
    """Agent specialized in coordinating workflow between other agents."""
    
    def __init__(
        self,
        client: Optional[OpenAI] = None,
        config: Optional[AgentConfig] = None,
    ):
        super().__init__(role="coordinator", client=client, config=config)
    
    def plan_workflow(self, task_description: str) -> str:
        """
        Plan a workflow for completing a task.
        
        Args:
            task_description: Description of the task to complete
            
        Returns:
            Workflow plan
        """
        task = (
            f"Create a workflow plan to complete the following task: {task_description}\n"
            f"Available agents: researcher, writer, reviewer.\n"
            f"Specify which agent should handle each step."
        )
        return self.execute(task)
    
    def decide_next_step(
        self,
        current_state: str,
        completed_steps: list,
    ) -> str:
        """
        Decide the next step in the workflow.
        
        Args:
            current_state: Current state of the workflow
            completed_steps: List of completed steps
            
        Returns:
            Decision on next step
        """
        task = (
            f"Current state: {current_state}\n"
            f"Completed steps: {', '.join(completed_steps)}\n"
            f"What should be the next step?"
        )
        return self.execute(task)
