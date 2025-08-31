#!/usr/bin/env python3
"""
Unit tests for XAgent integration components.
These tests run fast and locally without external dependencies.
"""

import pytest
import asyncio
import os
import sys
from unittest.mock import Mock, patch, AsyncMock
from typing import List, Dict, Any

# Add the server directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'apps', 'server'))

from agents.xagent import (
    AgentInterface, 
    AgentResult, 
    AgentFactory,
    XAgentAdapter, 
    LangchainReactAgent, 
    L3AGIToolAdapter
)
from memory.zep.zep_memory import ZepMemory
from services.run_log import RunLogsManager


class TestAgentResult:
    """Test the AgentResult dataclass"""
    
    def test_agent_result_creation(self):
        """Test creating AgentResult with various parameters"""
        result = AgentResult(
            final_answer="Test answer",
            tool_calls=[{"tool": "test", "args": {}}],
            running_records={"test": "data"},
            memory_updates={"key": "value"},
            voice_url="http://example.com/voice.mp3"
        )
        
        assert result.final_answer == "Test answer"
        assert len(result.tool_calls) == 1
        assert result.running_records["test"] == "data"
        assert result.memory_updates["key"] == "value"
        assert result.voice_url == "http://example.com/voice.mp3"
    
    def test_agent_result_minimal(self):
        """Test creating AgentResult with minimal parameters"""
        result = AgentResult(
            final_answer="Minimal answer",
            tool_calls=[]
        )
        
        assert result.final_answer == "Minimal answer"
        assert result.tool_calls == []
        assert result.running_records is None
        assert result.memory_updates is None
        assert result.voice_url is None


class TestL3AGIToolAdapter:
    """Test the tool adapter functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.adapter = L3AGIToolAdapter()
    
    def test_tool_mapping_creation(self):
        """Test that tool mapping is created correctly"""
        mapping = self.adapter.get_tool_mapping_info()
        
        # Should have mappings for all 26 L3AGI toolkits
        assert len(mapping) >= 26
        
        # Check specific mappings
        assert mapping["SerpGoogleSearch"] == "web_search"
        assert mapping["Twilio"] == "rapidapi_twilio"
        assert mapping["PostgresDatabaseTool"] == "database_postgres"
        assert mapping["Chart"] == "python_notebook"
    
    def test_rapidapi_tool_adaptation(self):
        """Test RapidAPI tool adaptation"""
        result = self.adapter.adapt_tool_call("Twilio", {
            "api_key": "test_key",
            "action": "send_sms",
            "to": "+1234567890",
            "message": "Test message"
        })
        
        assert result["tool"] == "rapidapi_twilio"
        assert result["args"]["api_key"] == "test_key"
        assert result["args"]["action"] == "send_sms"
        assert "to" in result["args"]["data"]
        assert "message" in result["args"]["data"]
    
    def test_web_search_tool_adaptation(self):
        """Test web search tool adaptation"""
        result = self.adapter.adapt_tool_call("SerpGoogleSearch", {
            "query": "AI news",
            "max_results": 5
        })
        
        assert result["tool"] == "web_search"
        assert result["args"]["query"] == "AI news"
        assert result["args"]["engine"] == "google"
        assert result["args"]["max_results"] == 5


class TestAgentFactory:
    """Test the agent factory functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        # Clear environment variables
        os.environ.pop("USE_XAGENT", None)
        os.environ.pop("FALLBACK_TO_REACT", None)
        os.environ.pop("HYBRID_MODE", None)
        
        self.factory = AgentFactory()
    
    def test_default_configuration(self):
        """Test default factory configuration"""
        info = self.factory.get_agent_info()
        
        assert info["use_xagent"] == False
        assert info["fallback_to_react"] == True
        assert info["hybrid_mode"] == False
        assert info["agent_type"] == "react"
    
    def test_environment_variable_override(self):
        """Test environment variable configuration override"""
        os.environ["USE_XAGENT"] = "true"
        os.environ["FALLBACK_TO_REACT"] = "false"
        
        factory = AgentFactory()
        info = factory.get_agent_info()
        
        assert info["use_xagent"] == True
        assert info["fallback_to_react"] == False
        assert info["agent_type"] == "xagent"
    
    def test_react_agent_creation(self):
        """Test creating ReAct agent"""
        mock_tools = [Mock(name="test_tool")]
        mock_llm = Mock()
        mock_memory = Mock(spec=ZepMemory)
        
        agent = self.factory.create_agent(
            agent_type="test",
            tools=mock_tools,
            llm=mock_llm,
            memory=mock_memory
        )
        
        assert isinstance(agent, LangchainReactAgent)
        assert agent.tools == mock_tools
        assert agent.llm == mock_llm
        assert agent.memory == mock_memory


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
