"""
Tests for the multi-agent workflow system.
"""
import pytest
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import AgentConfig


class TestConfiguration:
    """Test configuration settings."""
    
    def test_agent_roles_defined(self):
        """Test that all required agent roles are defined."""
        required_roles = ["researcher", "writer", "reviewer", "coordinator"]
        
        for role in required_roles:
            assert role in AgentConfig.AGENT_ROLES
            assert "name" in AgentConfig.AGENT_ROLES[role]
            assert "description" in AgentConfig.AGENT_ROLES[role]
            assert "instructions" in AgentConfig.AGENT_ROLES[role]
            assert "temperature" in AgentConfig.AGENT_ROLES[role]
    
    def test_temperature_ranges(self):
        """Test that temperature values are within valid range."""
        for role, config in AgentConfig.AGENT_ROLES.items():
            temp = config["temperature"]
            assert 0.0 <= temp <= 2.0, f"Temperature for {role} out of range: {temp}"
    
    def test_config_values(self):
        """Test configuration default values."""
        assert AgentConfig.MAX_RETRIES >= 0
        assert AgentConfig.TIMEOUT_SECONDS > 0


class TestAgentRoles:
    """Test agent role configurations."""
    
    def test_researcher_config(self):
        """Test researcher agent configuration."""
        config = AgentConfig.AGENT_ROLES["researcher"]
        assert config["name"] == "Research Agent"
        assert "research" in config["description"].lower()
    
    def test_writer_config(self):
        """Test writer agent configuration."""
        config = AgentConfig.AGENT_ROLES["writer"]
        assert config["name"] == "Writer Agent"
        assert "writer" in config["description"].lower() or "content" in config["description"].lower()
    
    def test_reviewer_config(self):
        """Test reviewer agent configuration."""
        config = AgentConfig.AGENT_ROLES["reviewer"]
        assert config["name"] == "Reviewer Agent"
        assert "review" in config["description"].lower()
    
    def test_coordinator_config(self):
        """Test coordinator agent configuration."""
        config = AgentConfig.AGENT_ROLES["coordinator"]
        assert config["name"] == "Coordinator Agent"
        assert "coordinat" in config["description"].lower() or "workflow" in config["description"].lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
