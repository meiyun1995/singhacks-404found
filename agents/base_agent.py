"""
Base agent class for the multi-agent workflow.
"""
from typing import Optional, Dict, Any, List
from openai import OpenAI
from config import AgentConfig


class BaseAgent:
    """Base class for all agents in the workflow."""
    
    def __init__(
        self,
        role: str,
        client: Optional[OpenAI] = None,
        config: Optional[AgentConfig] = None,
    ):
        """
        Initialize the base agent.
        
        Args:
            role: The role identifier for this agent (e.g., 'researcher', 'writer')
            client: Optional OpenAI client instance
            config: Optional configuration object
        """
        self.role = role
        self.config = config or AgentConfig()
        self.client = client or OpenAI(api_key=self.config.OPENAI_API_KEY)
        
        # Get role-specific configuration
        if role not in self.config.AGENT_ROLES:
            raise ValueError(f"Unknown agent role: {role}")
        
        self.role_config = self.config.AGENT_ROLES[role]
        self.name = self.role_config["name"]
        self.description = self.role_config["description"]
        self.instructions = self.role_config["instructions"]
        self.temperature = self.role_config["temperature"]
        
        self.conversation_history: List[Dict[str, str]] = []
    
    def create_message(self, content: str, role: str = "user") -> Dict[str, str]:
        """Create a message dictionary."""
        return {"role": role, "content": content}
    
    def add_to_history(self, message: Dict[str, str]) -> None:
        """Add a message to the conversation history."""
        self.conversation_history.append(message)
    
    def clear_history(self) -> None:
        """Clear the conversation history."""
        self.conversation_history = []
    
    def execute(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        use_history: bool = False,
    ) -> str:
        """
        Execute a task using the agent.
        
        Args:
            task: The task description or query
            context: Optional context information
            use_history: Whether to include conversation history
            
        Returns:
            The agent's response
        """
        messages = []
        
        # Add system message with instructions
        messages.append(self.create_message(self.instructions, "system"))
        
        # Add conversation history if requested
        if use_history and self.conversation_history:
            messages.extend(self.conversation_history)
        
        # Add context if provided
        if context:
            context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
            messages.append(
                self.create_message(f"Context:\n{context_str}", "system")
            )
        
        # Add the current task
        task_message = self.create_message(task, "user")
        messages.append(task_message)
        
        # Call OpenAI API
        try:
            response = self.client.chat.completions.create(
                model=self.config.OPENAI_MODEL,
                messages=messages,
                temperature=self.temperature,
            )
            
            result = response.choices[0].message.content
            
            # Update history if using it
            if use_history:
                self.add_to_history(task_message)
                self.add_to_history(self.create_message(result, "assistant"))
            
            return result
            
        except Exception as e:
            raise RuntimeError(f"Error executing task with {self.name}: {str(e)}")
    
    def __repr__(self) -> str:
        """String representation of the agent."""
        return f"{self.name} ({self.role})"
