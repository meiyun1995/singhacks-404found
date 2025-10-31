"""
Configuration settings for the multi-agent workflow.
"""
import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class AgentConfig:
    """Configuration for agent settings."""
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
    
    # Agent Settings
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    TIMEOUT_SECONDS: int = int(os.getenv("TIMEOUT_SECONDS", "60"))
    
    # Agent Definitions
    AGENT_ROLES: Dict[str, Dict[str, Any]] = {
        "researcher": {
            "name": "Research Agent",
            "description": "Conducts research and gathers information",
            "instructions": (
                "You are a research agent specialized in gathering and analyzing information. "
                "Your role is to find relevant data, facts, and insights on given topics. "
                "Provide comprehensive and well-structured research outputs."
            ),
            "temperature": 0.7,
        },
        "writer": {
            "name": "Writer Agent",
            "description": "Creates written content based on research",
            "instructions": (
                "You are a writer agent specialized in creating clear, engaging content. "
                "Your role is to transform research and information into well-written documents. "
                "Focus on clarity, coherence, and engaging narrative."
            ),
            "temperature": 0.8,
        },
        "reviewer": {
            "name": "Reviewer Agent",
            "description": "Reviews and provides feedback on content",
            "instructions": (
                "You are a reviewer agent specialized in quality assurance. "
                "Your role is to review content for accuracy, clarity, and quality. "
                "Provide constructive feedback and suggestions for improvement."
            ),
            "temperature": 0.5,
        },
        "coordinator": {
            "name": "Coordinator Agent",
            "description": "Coordinates the workflow between agents",
            "instructions": (
                "You are a coordinator agent that manages the workflow between different agents. "
                "Your role is to orchestrate tasks, manage handoffs, and ensure smooth collaboration. "
                "Make decisions about which agent should handle each task."
            ),
            "temperature": 0.3,
        },
    }
    
    @classmethod
    def validate(cls) -> bool:
        """Validate that required configuration is present."""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required but not set")
        return True
