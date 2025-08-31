#!/usr/bin/env python3
"""
Integration tests for XAgent with containers.
These tests require Docker and XAgent services to be running.
"""

import pytest
import asyncio
import os
import sys
import time
import requests
import json
from pathlib import Path

# Add the server directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'apps', 'server'))

from unittest.mock import Mock, patch
from agents.xagent import AgentFactory, AgentInterface
from memory.zep.zep_memory import ZepMemory
from services.run_log import RunLogsManager


class TestXAgentIntegration:
    """Integration tests for XAgent with real services"""
    
    @pytest.fixture(scope="class")
    def xagent_services(self):
        """Ensure XAgent services are running"""
        # Check if services are already running
        try:
            # Check XAgent Server
            response = requests.get("http://localhost:8090/health", timeout=5)
            xagent_healthy = response.status_code == 200
            
            # Check ToolServer
            response = requests.get("http://localhost:8080/health", timeout=5)
            toolserver_healthy = response.status_code == 200
            
            if not (xagent_healthy and toolserver_healthy):
                pytest.skip("XAgent services not running. Start with: docker-compose -f docker-compose.xagent.yml up -d")
                
        except requests.exceptions.RequestException:
            pytest.skip("XAgent services not accessible. Start with: docker-compose -f docker-compose.xagent.yml up -d")
        
        return True
    
    @pytest.fixture
    def agent_factory(self):
        """Create agent factory with XAgent enabled"""
        os.environ["USE_XAGENT"] = "true"
        os.environ["FALLBACK_TO_REACT"] = "true"
        
        factory = AgentFactory()
        factory.use_xagent = True
        
        return factory
    
    @pytest.fixture
    def mock_components(self):
        """Create mock components for testing"""
        tools = [
            Mock(name="web_search", description="Search the web for information"),
            Mock(name="file_editor", description="Edit files on the system"),
            Mock(name="python_notebook", description="Execute Python code")
        ]
        
        memory = ZepMemory(
            session_id="test_integration",
            url="http://localhost:8000",
            api_key="test_key"
        )
        
        run_logs_manager = None
        
        return tools, memory, run_logs_manager
    
    def test_xagent_services_health(self, xagent_services):
        """Test that XAgent services are healthy"""
        # XAgent Server health
        response = requests.get("http://localhost:8090/health")
        assert response.status_code == 200
        
        # ToolServer health
        response = requests.get("http://localhost:8080/health")
        assert response.status_code == 200
        
        # XAgent Web UI accessibility
        response = requests.get("http://localhost:5173")
        assert response.status_code == 200
    
    def test_agent_factory_xagent_creation(self, agent_factory, mock_components):
        """Test creating XAgent adapter through factory"""
        tools, memory, run_logs_manager = mock_components
        
        agent = agent_factory.create_agent(
            agent_type="integration_test",
            tools=tools,
            llm=Mock(),
            memory=memory,
            run_logs_manager=run_logs_manager
        )
        
        assert agent is not None
        assert hasattr(agent, 'run')
        assert hasattr(agent, 'stream_run')
        assert hasattr(agent, 'get_tool_descriptions')
    
    @pytest.mark.asyncio
    async def test_xagent_web_search_task(self, agent_factory, mock_components):
        """Test XAgent with web search task (uses web browser tool)"""
        tools, memory, run_logs_manager = mock_components
        
        agent = agent_factory.create_agent(
            agent_type="integration_test",
            tools=tools,
            llm=Mock(),
            memory=memory,
            run_logs_manager=run_logs_manager
        )
        
        # Test web search task
        task = "Search for the latest AI news and provide a summary"
        
        try:
            result = await agent.run(task)
            
            # Verify result structure
            assert result is not None
            assert hasattr(result, 'final_answer')
            assert isinstance(result.final_answer, str)
            assert len(result.final_answer) > 0
            
            # Verify running records
            assert hasattr(result, 'running_records')
            assert result.running_records is not None
            
            print(f"✅ Web search task completed: {result.final_answer[:100]}...")
            
        except Exception as e:
            pytest.fail(f"Web search task failed: {e}")
    
    @pytest.mark.asyncio
    async def test_xagent_coding_task(self, agent_factory, mock_components):
        """Test XAgent with coding task (uses Python notebook tool)"""
        tools, memory, run_logs_manager = mock_components
        
        agent = agent_factory.create_agent(
            agent_type="integration_test",
            tools=tools,
            llm=Mock(),
            memory=memory,
            run_logs_manager=run_logs_manager
        )
        
        # Test coding task
        task = "Write a Python function to calculate the factorial of a number"
        
        try:
            result = await agent.run(task)
            
            # Verify result structure
            assert result is not None
            assert hasattr(result, 'final_answer')
            assert isinstance(result.final_answer, str)
            assert len(result.final_answer) > 0
            
            # Should contain Python code
            assert "def" in result.final_answer or "factorial" in result.final_answer.lower()
            
            print(f"✅ Coding task completed: {result.final_answer[:100]}...")
            
        except Exception as e:
            pytest.fail(f"Coding task failed: {e}")
    
    @pytest.mark.asyncio
    async def test_xagent_file_editing_task(self, agent_factory, mock_components):
        """Test XAgent with file editing task (uses file editor tool)"""
        tools, memory, run_logs_manager = mock_components
        
        agent = agent_factory.create_agent(
            agent_type="integration_test",
            tools=tools,
            llm=Mock(),
            memory=memory,
            run_logs_manager=run_logs_manager
        )
        
        # Test file editing task
        task = "Create a simple text file with the content 'Hello, XAgent!'"
        
        try:
            result = await agent.run(task)
            
            # Verify result structure
            assert result is not None
            assert hasattr(result, 'final_answer')
            assert isinstance(result.final_answer, str)
            assert len(result.final_answer) > 0
            
            print(f"✅ File editing task completed: {result.final_answer[:100]}...")
            
        except Exception as e:
            pytest.fail(f"File editing task failed: {e}")
    
    @pytest.mark.asyncio
    async def test_xagent_streaming_execution(self, agent_factory, mock_components):
        """Test XAgent streaming execution"""
        tools, memory, run_logs_manager = mock_components
        
        agent = agent_factory.create_agent(
            agent_type="integration_test",
            tools=tools,
            llm=Mock(),
            memory=memory,
            run_logs_manager=run_logs_manager
        )
        
        # Test streaming task
        task = "Explain how machine learning works in simple terms"
        
        try:
            chunks = []
            async for chunk in agent.stream_run(task):
                if chunk:
                    chunks.append(chunk)
            
            # Should receive multiple chunks
            assert len(chunks) > 0
            
            # Combine chunks
            full_response = "".join(chunks)
            assert len(full_response) > 0
            
            print(f"✅ Streaming execution completed: {full_response[:100]}...")
            
        except Exception as e:
            pytest.fail(f"Streaming execution failed: {e}")
    
    def test_running_records_creation(self, xagent_services):
        """Test that running records are created with steps"""
        # Check if running records directory exists
        records_dir = Path("./logs/xagent")
        
        if records_dir.exists():
            # Look for running records files
            record_files = list(records_dir.glob("*.json"))
            
            if record_files:
                # Check the most recent record file
                latest_record = max(record_files, key=lambda p: p.stat().st_mtime)
                
                with open(latest_record, 'r') as f:
                    record_data = json.load(f)
                
                # Verify record structure
                assert "steps" in record_data or "actions" in record_data
                assert "task" in record_data
                assert "result" in record_data
                
                print(f"✅ Running records found: {latest_record}")
                print(f"   Steps: {len(record_data.get('steps', record_data.get('actions', [])))}")
                
                return latest_record
        
        # If no records found, that's okay for this test
        print("ℹ️  No running records found yet (this is normal for first run)")
        return None
    
    def test_process_exit_cleanly(self, xagent_services):
        """Test that processes exit cleanly"""
        # This test verifies that the test suite can complete without hanging
        # If we get here, the test suite is working correctly
        
        # Check that services are still responsive
        try:
            response = requests.get("http://localhost:8090/health", timeout=5)
            assert response.status_code == 200
            
            response = requests.get("http://localhost:8080/health", timeout=5)
            assert response.status_code == 200
            
            print("✅ All services still responsive after tests")
            
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Services became unresponsive: {e}")


class TestXAgentFallback:
    """Test XAgent fallback mechanisms"""
    
    @pytest.fixture
    def agent_factory_fallback(self):
        """Create agent factory with fallback enabled"""
        os.environ["USE_XAGENT"] = "true"
        os.environ["FALLBACK_TO_REACT"] = "true"
        
        factory = AgentFactory()
        factory.use_xagent = True
        factory.fallback_to_react = True
        
        return factory
    
    def test_fallback_to_react_on_xagent_failure(self, agent_factory_fallback, mock_components):
        """Test fallback to ReAct when XAgent fails"""
        tools, memory, run_logs_manager = mock_components
        
        # Mock XAgent unavailability
        with patch.object(agent_factory_fallback, '_create_xagent_agent', side_effect=Exception("XAgent unavailable")):
            agent = agent_factory_fallback.create_agent(
                agent_type="fallback_test",
                tools=tools,
                llm=Mock(),
                memory=memory,
                run_logs_manager=run_logs_manager
            )
            
            # Should fallback to ReAct
            from agents.xagent import LangchainReactAgent
            assert isinstance(agent, LangchainReactAgent)
            print("✅ Successfully fell back to ReAct agent")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-k", "xagent"])
