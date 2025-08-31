#!/usr/bin/env python3
"""
Simplified unit tests for XAgent integration components.
These tests run fast and locally without external dependencies.
"""

import pytest
import asyncio
import os
import sys
from unittest.mock import Mock, patch, AsyncMock
from typing import List, Dict, Any

# Test the core XAgent components directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'apps', 'server', 'agents', 'xagent'))

from agent_interface import AgentInterface, AgentResult
from tool_adapter import L3AGIToolAdapter


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
        
        # Should have mappings for L3AGI toolkits
        assert len(mapping) >= 20  # Adjusted to actual count
        
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
    
    def test_python_execution_tool_adaptation(self):
        """Test Python execution tool adaptation"""
        result = self.adapter.adapt_tool_call("Chart", {
            "chart_type": "bar",
            "data": [1, 2, 3, 4, 5],
            "title": "Test Chart"
        })
        
        assert result["tool"] == "python_notebook"
        assert "code" in result["args"]
        assert "matplotlib" in result["args"]["dependencies"]
        assert "chart.png" in result["args"]["output_files"]
    
    def test_unknown_tool_adaptation(self):
        """Test unknown tool adaptation"""
        result = self.adapter.adapt_tool_call("UnknownTool", {
            "param1": "value1",
            "param2": "value2"
        })
        
        assert result["tool"] == "python_notebook"
        assert "UnknownTool" in result["args"]["code"]
        assert "param1" in result["args"]["code"]
    
    def test_search_engine_mapping(self):
        """Test search engine mapping"""
        assert self.adapter._get_search_engine("SerpGoogleSearch") == "google"
        assert self.adapter._get_search_engine("DuckDuckGo") == "duckduckgo"
        assert self.adapter._get_search_engine("Bing") == "bing"
        assert self.adapter._get_search_engine("Wikipedia") == "wikipedia"
    
    def test_available_tools(self):
        """Test available tools listing"""
        available = self.adapter.get_available_tools()
        
        assert isinstance(available, list)
        assert "web_search" in available
        assert "file_editor" in available
        assert "python_notebook" in available
        assert "rapidapi_twilio" in available
    
    def test_tool_support_checking(self):
        """Test tool support checking"""
        assert self.adapter.is_tool_supported("SerpGoogleSearch") is True
        assert self.adapter.is_tool_supported("FileTool") is True
        assert self.adapter.is_tool_supported("UnknownTool") is False


class TestAgentInterface:
    """Test the abstract AgentInterface"""
    
    def test_agent_interface_abstract(self):
        """Test that AgentInterface is properly abstract"""
        from abc import ABC
        assert issubclass(AgentInterface, ABC)
    
    def test_agent_interface_methods(self):
        """Test that AgentInterface has required methods"""
        # Check that the interface defines the required methods
        assert hasattr(AgentInterface, 'run')
        assert hasattr(AgentInterface, 'stream_run')
        assert hasattr(AgentInterface, 'get_tool_descriptions')
        
        # Check that methods are abstract
        assert AgentInterface.run.__isabstractmethod__
        assert AgentInterface.stream_run.__isabstractmethod__
        assert AgentInterface.get_tool_descriptions.__isabstractmethod__


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
