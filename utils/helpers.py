"""
Utility functions for the multi-agent workflow.
"""
import json
import os
from typing import Any, Dict
from datetime import datetime


def save_to_json(data: Dict[str, Any], filename: str, directory: str = "outputs") -> str:
    """
    Save data to a JSON file.
    
    Args:
        data: Data to save
        filename: Name of the file (without extension)
        directory: Directory to save the file in
        
    Returns:
        Full path to the saved file
    """
    # Create directory if it doesn't exist
    os.makedirs(directory, exist_ok=True)
    
    # Add timestamp to filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    full_filename = f"{filename}_{timestamp}.json"
    filepath = os.path.join(directory, full_filename)
    
    # Save to file
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    return filepath


def load_from_json(filepath: str) -> Dict[str, Any]:
    """
    Load data from a JSON file.
    
    Args:
        filepath: Path to the JSON file
        
    Returns:
        Loaded data
    """
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def format_agent_response(agent_name: str, response: str, max_length: int = 500) -> str:
    """
    Format an agent response for display.
    
    Args:
        agent_name: Name of the agent
        response: The response text
        max_length: Maximum length to display
        
    Returns:
        Formatted response string
    """
    truncated = response[:max_length] + "..." if len(response) > max_length else response
    return f"[{agent_name}]\n{truncated}\n"


def create_workflow_summary(results: Dict[str, Any]) -> str:
    """
    Create a summary of workflow results.
    
    Args:
        results: Workflow results dictionary
        
    Returns:
        Formatted summary string
    """
    summary_lines = ["=== Workflow Summary ===\n"]
    
    for key, value in results.items():
        if isinstance(value, str):
            length = len(value)
            preview = value[:100] + "..." if length > 100 else value
            summary_lines.append(f"{key}:")
            summary_lines.append(f"  Length: {length} characters")
            summary_lines.append(f"  Preview: {preview}\n")
        else:
            summary_lines.append(f"{key}: {value}\n")
    
    return "\n".join(summary_lines)


def validate_environment() -> bool:
    """
    Validate that required environment variables are set.
    
    Returns:
        True if environment is valid
        
    Raises:
        ValueError if required variables are missing
    """
    required_vars = ["OPENAI_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing_vars)}\n"
            "Please set them in your .env file or environment."
        )
    
    return True
