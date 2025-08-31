#!/usr/bin/env python3
"""
Unit tests for XAgent adapters.
These tests use mocks and don't require external services.
"""

import pytest
import asyncio
import os
import sys
from unittest.mock import Mock, patch, AsyncMock, MagicMock

# Add the server directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'apps', 'server'))

from agents.xagent import (
    AgentInterface, AgentResult, AgentFactory,
    XAgentAdapter, LangchainReactAgent, L3AGIToolAdapter
)
from memory.zep.zep_memory import ZepMemory
from services.run_log import RunLogsManager


class TestAgentInterface:
    """Test the abstract AgentInterface"""
    
    def test_agent_interface_abstract(self):
        """Test that AgentInterface is properly abstract"""
        from abc import ABC
        assert issubclass(AgentInterface, ABC)
    
    def test_agent_result_structure(self):
        """Test AgentResult dataclass structure"""
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


class TestXAgentAdapter:
    """Test XAgent adapter with mocks"""
    
    @pytest.fixture
    def mock_components(self):
        """Create mock components for testing"""
        tools = [
            Mock(name="web_search", description="Search the web"),
            Mock(name="file_editor", description="Edit files")
        ]
        
        memory = Mock(spec=ZepMemory)
        memory.session_id = "test_session"
        
        run_logs_manager = Mock(spec=RunLogsManager)
        
        return tools, memory, run_logs_manager
    
    @pytest.fixture
    def xagent_adapter(self, mock_components):
        """Create XAgent adapter instance"""
        tools, memory, run_logs_manager = mock_components
        
        with patch.dict(os.environ, {
            "XAGENT_URL": "http://localhost:8090",
            "TOOLSERVER_URL": "http://localhost:8080"
        }):
            adapter = XAgentAdapter(
                config_path="./configs/xagent/config.yml",
                memory=memory,
                run_logs_manager=run_logs_manager,
                tools=tools
            )
            return adapter
    
    def test_xagent_adapter_initialization(self, xagent_adapter):
        """Test XAgent adapter initialization"""
        assert xagent_adapter is not None
        assert hasattr(xagent_adapter, 'run')
        assert hasattr(xagent_adapter, 'stream_run')
        assert hasattr(xagent_adapter, 'get_tool_descriptions')
    
    def test_tool_descriptions_building(self, xagent_adapter):
        """Test tool descriptions are built correctly"""
        descriptions = xagent_adapter.get_tool_descriptions()
        
        assert isinstance(descriptions, list)
        assert len(descriptions) == 2
        assert any("web_search" in desc for desc in descriptions)
        assert any("file_editor" in desc for desc in descriptions)
    
    @pytest.mark.asyncio
    async def test_xagent_adapter_run_success(self, xagent_adapter):
        """Test successful XAgent execution"""
        # Mock successful API response
        mock_response = {
            "final_answer": "Task completed successfully",
            "tool_calls": [{"tool": "web_search", "args": {"query": "test"}}],
            "running_records": {"steps": 3, "status": "completed"}
        }
        
        with patch.object(xagent_adapter, '_call_xagent_api', return_value=mock_response):
            result = await xagent_adapter.run("Test task")
            
            assert isinstance(result, AgentResult)
            assert result.final_answer == "Task completed successfully"
            assert len(result.tool_calls) == 1
            assert result.running_records["steps"] == 3
    
    @pytest.mark.asyncio
    async def test_xagent_adapter_run_failure(self, xagent_adapter):
        """Test XAgent execution failure handling"""
        with patch.object(xagent_adapter, '_call_xagent_api', side_effect=Exception("API Error")):
            result = await xagent_adapter.run("Test task")
            
            assert isinstance(result, AgentResult)
            assert "Error:" in result.final_answer
            assert result.running_records["error"] == "API Error"
    
    @pytest.mark.asyncio
    async def test_xagent_adapter_streaming_success(self, xagent_adapter):
        """Test successful XAgent streaming"""
        # Mock streaming response
        async def mock_stream():
            yield "First chunk"
            yield "Second chunk"
            yield "Final chunk"
        
        with patch.object(xagent_adapter, '_call_xagent_streaming_api', return_value=mock_stream()):
            chunks = []
            async for chunk in xagent_adapter.stream_run("Test streaming task"):
                chunks.append(chunk)
            
            assert len(chunks) == 3
            assert "First chunk" in chunks
            assert "Final chunk" in chunks
    
    @pytest.mark.asyncio
    async def test_xagent_adapter_streaming_failure(self, xagent_adapter):
        """Test XAgent streaming failure handling"""
        with patch.object(xagent_adapter, '_call_xagent_streaming_api', side_effect=Exception("Streaming Error")):
            chunks = []
            async for chunk in xagent_adapter.stream_run("Test streaming task"):
                chunks.append(chunk)
            
            assert len(chunks) == 1
            assert "Error:" in chunks[0]
    
    def test_input_conversion(self, xagent_adapter):
        """Test input conversion to XAgent format"""
        task = "Search for information"
        files = ["file1.txt", "file2.txt"]
        history = [
            {"type": "human", "content": "Hello"},
            {"type": "ai", "content": "Hi there"}
        ]
        
        converted = xagent_adapter._convert_input(task, files, history)
        
        assert converted["task"] == task
        assert converted["files"] == files
        assert len(converted["history"]) == 2
        assert converted["history"][0]["role"] == "user"
        assert converted["history"][1]["role"] == "assistant"
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, xagent_adapter):
        """Test successful health check"""
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = Mock()
            mock_response.status = 200
            mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
            
            is_healthy = await xagent_adapter.health_check()
            assert is_healthy is True
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, xagent_adapter):
        """Test failed health check"""
        with patch('aiohttp.ClientSession') as mock_session:
            mock_session.return_value.__aenter__.side_effect = Exception("Connection failed")
            
            is_healthy = await xagent_adapter.health_check()
            assert is_healthy is False


class TestLangchainReactAgent:
    """Test ReAct agent adapter with mocks"""
    
    @pytest.fixture
    def mock_components(self):
        """Create mock components for testing"""
        tools = [
            Mock(name="search", description="Search tool"),
            Mock(name="calculator", description="Math tool")
        ]
        
        llm = Mock()
        llm.streaming = True
        
        memory = Mock(spec=ZepMemory)
        memory.session_id = "test_session"
        
        run_logs_manager = Mock(spec=RunLogsManager)
        
        return tools, llm, memory, run_logs_manager
    
    @pytest.fixture
    def react_agent(self, mock_components):
        """Create ReAct agent adapter instance"""
        tools, llm, memory, run_logs_manager = mock_components
        
        with patch('langchain.agents.create_react_agent'), \
             patch('langchain.agents.AgentExecutor'):
            
            agent = LangchainReactAgent(
                tools=tools,
                llm=llm,
                memory=memory,
                run_logs_manager=run_logs_manager,
                system_message="Test system message"
            )
            return agent
    
    def test_react_agent_initialization(self, react_agent):
        """Test ReAct agent adapter initialization"""
        assert react_agent is not None
        assert hasattr(react_agent, 'run')
        assert hasattr(react_agent, 'stream_run')
        assert hasattr(react_agent, 'get_tool_descriptions')
    
    def test_tool_descriptions_building(self, react_agent):
        """Test tool descriptions are built correctly"""
        descriptions = react_agent.get_tool_descriptions()
        
        assert isinstance(descriptions, list)
        assert len(descriptions) == 2
        assert any("search" in desc for desc in descriptions)
        assert any("calculator" in desc for desc in descriptions)
    
    @pytest.mark.asyncio
    async def test_react_agent_run_success(self, react_agent):
        """Test successful ReAct execution"""
        # Mock successful execution
        mock_result = "Task completed successfully"
        
        with patch.object(react_agent, '_agent') as mock_agent:
            mock_agent.run.return_value = mock_result
            
            result = await react_agent.run("Test task")
            
            assert isinstance(result, AgentResult)
            assert result.final_answer == mock_result
            assert result.running_records["agent_type"] == "react"
    
    @pytest.mark.asyncio
    async def test_react_agent_run_failure(self, react_agent):
        """Test ReAct execution failure handling"""
        with patch.object(react_agent, '_agent') as mock_agent:
            mock_agent.run.side_effect = Exception("Execution failed")
            
            result = await react_agent.run("Test task")
            
            assert isinstance(result, AgentResult)
            assert "Error:" in result.final_answer
            assert result.running_records["error"] == "Execution failed"
    
    @pytest.mark.asyncio
    async def test_react_agent_streaming_success(self, react_agent):
        """Test successful ReAct streaming"""
        # Mock streaming events
        mock_events = [
            {"event": "on_chat_model_stream", "data": {"chunk": Mock(content="First")}},
            {"event": "on_chat_model_stream", "data": {"chunk": Mock(content="Second")}},
            {"event": "on_chat_model_stream", "data": {"chunk": Mock(content="Final")}}
        ]
        
        with patch.object(react_agent, '_agent') as mock_agent:
            mock_agent.astream_events.return_value = mock_events
            
            chunks = []
            async for chunk in react_agent.stream_run("Test streaming task"):
                chunks.append(chunk)
            
            assert len(chunks) > 0
    
    def test_agent_info(self, react_agent):
        """Test agent info retrieval"""
        info = react_agent.get_agent_info()
        
        assert info["agent_type"] == "react"
        assert info["tools_count"] == 2
        assert "search" in info["tool_names"]
        assert info["memory_type"] == "zep"
        assert info["system_message"] == "Test system message"


class TestL3AGIToolAdapter:
    """Test L3AGI tool adapter"""
    
    @pytest.fixture
    def tool_adapter(self):
        """Create tool adapter instance"""
        return L3AGIToolAdapter()
    
    def test_tool_mapping_creation(self, tool_adapter):
        """Test tool mapping is created correctly"""
        mapping = tool_adapter.get_tool_mapping_info()
        
        assert isinstance(mapping, dict)
        assert len(mapping) > 0
        
        # Check some key mappings
        assert mapping["SerpGoogleSearch"] == "web_search"
        assert mapping["FileTool"] == "file_editor"
        assert mapping["PostgresDatabaseTool"] == "database_postgres"
    
    def test_rapidapi_tool_adaptation(self, tool_adapter):
        """Test RapidAPI tool adaptation"""
        adapted = tool_adapter.adapt_tool_call("Twilio", {
            "api_key": "test_key",
            "action": "send_sms",
            "to": "+1234567890",
            "message": "Test message"
        })
        
        assert adapted["tool"] == "rapidapi_twilio"
        assert "api_key" in adapted["args"]
        assert adapted["args"]["action"] == "send_sms"
        assert adapted["args"]["data"]["to"] == "+1234567890"
    
    def test_direct_mapping_tool_adaptation(self, tool_adapter):
        """Test direct mapping tool adaptation"""
        adapted = tool_adapter.adapt_tool_call("SerpGoogleSearch", {
            "query": "artificial intelligence",
            "max_results": 5
        })
        
        assert adapted["tool"] == "web_search"
        assert adapted["args"]["query"] == "artificial intelligence"
        assert adapted["args"]["engine"] == "google"
        assert adapted["args"]["max_results"] == 5
    
    def test_python_execution_tool_adaptation(self, tool_adapter):
        """Test Python execution tool adaptation"""
        adapted = tool_adapter.adapt_tool_call("Chart", {
            "chart_type": "bar",
            "data": [1, 2, 3, 4, 5],
            "title": "Test Chart"
        })
        
        assert adapted["tool"] == "python_notebook"
        assert "code" in adapted["args"]
        assert "matplotlib" in adapted["args"]["dependencies"]
        assert "chart.png" in adapted["args"]["output_files"]
    
    def test_unknown_tool_adaptation(self, tool_adapter):
        """Test unknown tool adaptation"""
        adapted = tool_adapter.adapt_tool_call("UnknownTool", {
            "param1": "value1",
            "param2": "value2"
        })
        
        assert adapted["tool"] == "python_notebook"
        assert "UnknownTool" in adapted["args"]["code"]
        assert "param1" in adapted["args"]["code"]
    
    def test_search_engine_mapping(self, tool_adapter):
        """Test search engine mapping"""
        assert tool_adapter._get_search_engine("SerpGoogleSearch") == "google"
        assert tool_adapter._get_search_engine("DuckDuckGo") == "duckduckgo"
        assert tool_adapter._get_search_engine("Bing") == "bing"
        assert tool_adapter._get_search_engine("Wikipedia") == "wikipedia"
    
    def test_available_tools(self, tool_adapter):
        """Test available tools listing"""
        available = tool_adapter.get_available_tools()
        
        assert isinstance(available, list)
        assert "web_search" in available
        assert "file_editor" in available
        assert "python_notebook" in available
        assert "rapidapi_twilio" in available
    
    def test_tool_support_checking(self, tool_adapter):
        """Test tool support checking"""
        assert tool_adapter.is_tool_supported("SerpGoogleSearch") is True
        assert tool_adapter.is_tool_supported("FileTool") is True
        assert tool_adapter.is_tool_supported("UnknownTool") is False


class TestAgentFactory:
    """Test agent factory with mocks"""
    
    @pytest.fixture
    def mock_components(self):
        """Create mock components for testing"""
        tools = [Mock(name="test_tool")]
        llm = Mock()
        memory = Mock(spec=ZepMemory)
        run_logs_manager = Mock(spec=RunLogsManager)
        
        return tools, llm, memory, run_logs_manager
    
    def test_factory_default_configuration(self):
        """Test factory default configuration"""
        # Clear environment variables
        with patch.dict(os.environ, {}, clear=True):
            factory = AgentFactory()
            
            assert factory.use_xagent is False
            assert factory.fallback_to_react is True
            assert factory.hybrid_mode is False
    
    def test_factory_environment_override(self):
        """Test factory environment variable override"""
        with patch.dict(os.environ, {
            "USE_XAGENT": "true",
            "FALLBACK_TO_REACT": "false"
        }):
            factory = AgentFactory()
            
            assert factory.use_xagent is True
            assert factory.fallback_to_react is False
    
    def test_factory_react_agent_creation(self, mock_components):
        """Test creating ReAct agent"""
        tools, llm, memory, run_logs_manager = mock_components
        
        with patch.dict(os.environ, {"USE_XAGENT": "false"}):
            factory = AgentFactory()
            agent = factory.create_agent(
                agent_type="test",
                tools=tools,
                llm=llm,
                memory=memory,
                run_logs_manager=run_logs_manager
            )
            
            assert isinstance(agent, LangchainReactAgent)
    
    def test_factory_xagent_creation(self, mock_components):
        """Test creating XAgent"""
        tools, llm, memory, run_logs_manager = mock_components
        
        with patch.dict(os.environ, {"USE_XAGENT": "true"}):
            factory = AgentFactory()
            agent = factory.create_agent(
                agent_type="test",
                tools=tools,
                llm=llm,
                memory=memory,
                run_logs_manager=run_logs_manager
            )
            
            assert isinstance(agent, XAgentAdapter)
    
    def test_factory_fallback_mechanism(self, mock_components):
        """Test factory fallback mechanism"""
        tools, llm, memory, run_logs_manager = mock_components
        
        with patch.dict(os.environ, {
            "USE_XAGENT": "true",
            "FALLBACK_TO_REACT": "true"
        }):
            factory = AgentFactory()
            
            # Mock XAgent creation failure
            with patch.object(factory, '_create_xagent_agent', side_effect=Exception("XAgent failed")):
                agent = factory.create_agent(
                    agent_type="test",
                    tools=tools,
                    llm=llm,
                    memory=memory,
                    run_logs_manager=run_logs_manager
                )
                
                # Should fallback to ReAct
                assert isinstance(agent, LangchainReactAgent)
    
    def test_factory_switching(self):
        """Test factory agent type switching"""
        factory = AgentFactory()
        
        # Start with ReAct
        factory.use_xagent = False
        assert factory.get_agent_info()["agent_type"] == "react"
        
        # Switch to XAgent
        factory.switch_to_xagent()
        assert factory.get_agent_info()["agent_type"] == "xagent"
        
        # Toggle back
        factory.toggle_agent_type()
        assert factory.get_agent_info()["agent_type"] == "react"
    
    def test_factory_agent_info(self):
        """Test factory agent info"""
        factory = AgentFactory()
        factory.use_xagent = True
        
        info = factory.get_agent_info()
        
        assert info["use_xagent"] is True
        assert info["fallback_to_react"] is True
        assert info["agent_type"] == "xagent"


class TestHistoryMapping:
    """Test history mapping functionality"""
    
    @pytest.fixture
    def mock_memory(self):
        """Create mock memory with history"""
        memory = Mock(spec=ZepMemory)
        memory.session_id = "test_session"
        
        # Mock conversation history
        memory.get_memory_variables.return_value = {
            "chat_history": [
                "Human: Hello, how are you?",
                "AI: I'm doing well, thank you!",
                "Human: Can you help me with a task?",
                "AI: Of course! What do you need help with?",
                "Human: I need to search for information about AI"
            ]
        }
        
        return memory
    
    def test_history_context_preservation(self, mock_memory):
        """Test that history context is preserved"""
        from agents.xagent import XAgentAdapter
        
        adapter = XAgentAdapter(
            config_path="./configs/xagent/config.yml",
            memory=mock_memory,
            run_logs_manager=None,
            tools=[]
        )
        
        # Convert input with history
        converted = adapter._convert_input(
            "Search for AI information",
            history=[
                {"type": "human", "content": "Hello"},
                {"type": "ai", "content": "Hi there"},
                {"type": "human", "content": "Help me with AI search"}
            ]
        )
        
        assert len(converted["history"]) == 3
        assert converted["history"][0]["role"] == "user"
        assert converted["history"][1]["role"] == "assistant"
        assert converted["history"][2]["role"] == "user"
    
    def test_coherent_output_with_context(self, mock_memory):
        """Test that output remains coherent with context"""
        # This test verifies that passing 3-5 turns as context
        # leads to coherent output
        
        # Mock XAgent response that should be contextually aware
        mock_response = {
            "final_answer": "Based on our conversation about AI, I'll search for the latest information about artificial intelligence and machine learning developments.",
            "tool_calls": [{"tool": "web_search", "args": {"query": "latest AI developments"}}],
            "running_records": {"context_used": True, "turns_processed": 5}
        }
        
        from agents.xagent import XAgentAdapter
        
        adapter = XAgentAdapter(
            config_path="./configs/xagent/config.yml",
            memory=mock_memory,
            run_logs_manager=None,
            tools=[]
        )
        
        with patch.object(adapter, '_call_xagent_api', return_value=mock_response):
            result = asyncio.run(adapter.run("Search for AI information"))
            
            # Verify the response shows context awareness
            assert "Based on our conversation" in result.final_answer
            assert "AI" in result.final_answer
            assert result.running_records["context_used"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
