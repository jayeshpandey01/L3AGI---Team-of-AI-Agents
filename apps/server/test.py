import os
import asyncio
import logging
from typing import List, Dict, Any

from langchain_community.chat_models import ChatOpenAI
from agents.xagent import AgentFactory, AgentInterface
from memory.zep.zep_memory import ZepMemory
from services.run_log import RunLogsManager

logger = logging.getLogger(__name__)


def agent_factory():
    """Factory function that creates either ReAct or XAgent based on environment variable"""
    
    # Check which agent implementation to use
    agent_impl = os.getenv("AGENT_IMPL", "react").lower()
    
    # Create mock components for testing
    llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo")
    tools = []  # Empty tools for basic testing
    memory = ZepMemory(
        session_id="test_session",
        url="http://localhost:8000",
        api_key="test_key"
    )
    run_logs_manager = None
    
    # Create agent factory
    agent_factory = AgentFactory()
    
    if agent_impl == "xagent":
        # Force XAgent usage
        agent_factory.use_xagent = True
        logger.info("Using XAgent implementation for testing")
    else:
        # Use ReAct (default)
        agent_factory.use_xagent = False
        logger.info("Using ReAct implementation for testing")
    
    # Create and return the appropriate agent
    agent = agent_factory.create_agent(
        agent_type="test",
        tools=tools,
        llm=llm,
        memory=memory,
        run_logs_manager=run_logs_manager
    )
    
    return agent


async def test_agent_basic_functionality():
    """Test basic agent functionality"""
    
    agent = agent_factory()
    
    # Test basic properties
    assert agent is not None, "Agent should be created successfully"
    assert hasattr(agent, 'run'), "Agent should have run method"
    assert hasattr(agent, 'stream_run'), "Agent should have stream_run method"
    assert hasattr(agent, 'get_tool_descriptions'), "Agent should have get_tool_descriptions method"
    
    # Test tool descriptions
    tool_descriptions = agent.get_tool_descriptions()
    assert isinstance(tool_descriptions, list), "Tool descriptions should be a list"
    
    # Test basic execution
    test_prompt = "Hello, this is a test message."
    
    try:
        result = await agent.run(test_prompt)
        assert result is not None, "Agent should return a result"
        assert hasattr(result, 'final_answer'), "Result should have final_answer attribute"
        assert isinstance(result.final_answer, str), "Final answer should be a string"
        assert len(result.final_answer) > 0, "Final answer should not be empty"
        
        logger.info(f"✅ Basic functionality test passed. Agent type: {type(agent).__name__}")
        logger.info(f"✅ Final answer: {result.final_answer[:100]}...")
        
    except Exception as e:
        logger.error(f"❌ Basic functionality test failed: {e}")
        raise


async def test_agent_streaming():
    """Test agent streaming functionality"""
    
    agent = agent_factory()
    test_prompt = "Provide a brief response to this test."
    
    try:
        chunks = []
        async for chunk in agent.stream_run(test_prompt):
            if chunk:
                chunks.append(chunk)
        
        assert len(chunks) > 0, "Should receive at least one chunk"
        combined_response = "".join(chunks)
        assert len(combined_response) > 0, "Combined response should not be empty"
        
        logger.info(f"✅ Streaming test passed. Received {len(chunks)} chunks")
        logger.info(f"✅ Combined response: {combined_response[:100]}...")
        
    except Exception as e:
        logger.error(f"❌ Streaming test failed: {e}")
        raise


async def test_agent_fallback():
    """Test agent fallback functionality"""
    
    # Test with XAgent unavailable (should fallback to ReAct)
    original_use_xagent = os.getenv("USE_XAGENT")
    os.environ["USE_XAGENT"] = "true"
    os.environ["FALLBACK_TO_REACT"] = "true"
    
    try:
        agent_factory = AgentFactory()
        agent = agent_factory.create_agent(
            agent_type="test",
            tools=[],
            llm=ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo"),
            memory=ZepMemory(session_id="test", url="http://localhost:8000", api_key="test"),
            run_logs_manager=None
        )
        
        # Should fallback to ReAct if XAgent fails
        assert agent is not None, "Agent should be created even with fallback"
        logger.info(f"✅ Fallback test passed. Agent type: {type(agent).__name__}")
        
    finally:
        # Restore original environment
        if original_use_xagent:
            os.environ["USE_XAGENT"] = original_use_xagent
        else:
            os.environ.pop("USE_XAGENT", None)
        os.environ.pop("FALLBACK_TO_REACT", None)


async def run_all_tests():
    """Run all agent tests"""
    
    logger.info("🚀 Starting agent functionality tests...")
    
    try:
        await test_agent_basic_functionality()
        await test_agent_streaming()
        await test_agent_fallback()
        
        logger.info("✅ All tests passed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Tests failed: {e}")
        raise


# Run tests if this file is executed directly
if __name__ == "__main__":
    asyncio.run(run_all_tests())
