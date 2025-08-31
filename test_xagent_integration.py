#!/usr/bin/env python3
"""
Simple test script to verify XAgent integration works correctly.
Run this script to test the basic functionality.
"""

import os
import sys
import asyncio
import logging

# Add the server directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'apps', 'server'))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_basic_imports():
    """Test that all required modules can be imported"""
    
    logger.info("Testing basic imports...")
    
    try:
        from agents.xagent import AgentInterface, AgentResult, AgentFactory
        from agents.xagent import XAgentAdapter, LangchainReactAgent, L3AGIToolAdapter
        
        logger.info("✅ All XAgent modules imported successfully")
        return True
        
    except ImportError as e:
        logger.error(f"❌ Import failed: {e}")
        return False


async def test_agent_factory():
    """Test the agent factory creation"""
    
    logger.info("Testing agent factory...")
    
    try:
        from agents.xagent import AgentFactory
        
        # Test with ReAct (default)
        factory = AgentFactory()
        logger.info(f"✅ AgentFactory created: {factory.get_agent_info()}")
        
        # Test switching
        factory.switch_to_xagent()
        logger.info(f"✅ Switched to XAgent: {factory.get_agent_info()}")
        
        factory.switch_to_react()
        logger.info(f"✅ Switched to ReAct: {factory.get_agent_info()}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Agent factory test failed: {e}")
        return False


async def test_tool_adapter():
    """Test the tool adapter functionality"""
    
    logger.info("Testing tool adapter...")
    
    try:
        from agents.xagent import L3AGIToolAdapter
        
        adapter = L3AGIToolAdapter()
        
        # Test tool mapping
        mapping = adapter.get_tool_mapping_info()
        logger.info(f"✅ Tool mapping created: {len(mapping)} tools mapped")
        
        # Test specific tool adaptation
        search_tool = adapter.adapt_tool_call("SerpGoogleSearch", {"query": "test"})
        logger.info(f"✅ Search tool adapted: {search_tool}")
        
        # Test available tools
        available_tools = adapter.get_available_tools()
        logger.info(f"✅ Available tools: {available_tools}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Tool adapter test failed: {e}")
        return False


async def test_agent_interface():
    """Test the agent interface structure"""
    
    logger.info("Testing agent interface...")
    
    try:
        from agents.xagent import AgentInterface, AgentResult
        
        # Test AgentResult creation
        result = AgentResult(
            final_answer="Test answer",
            tool_calls=[],
            running_records={"test": "data"}
        )
        
        logger.info(f"✅ AgentResult created: {result.final_answer}")
        
        # Test that AgentInterface is abstract
        from abc import ABC
        assert issubclass(AgentInterface, ABC), "AgentInterface should be abstract"
        logger.info("✅ AgentInterface is properly abstract")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Agent interface test failed: {e}")
        return False


async def test_environment_variables():
    """Test environment variable configuration"""
    
    logger.info("Testing environment variables...")
    
    # Test default values
    os.environ.pop("USE_XAGENT", None)
    os.environ.pop("FALLBACK_TO_REACT", None)
    os.environ.pop("HYBRID_MODE", None)
    
    from agents.xagent import AgentFactory
    
    factory = AgentFactory()
    info = factory.get_agent_info()
    
    logger.info(f"✅ Default configuration: {info}")
    
    # Test environment variable override
    os.environ["USE_XAGENT"] = "true"
    factory2 = AgentFactory()
    info2 = factory2.get_agent_info()
    
    logger.info(f"✅ Environment override: {info2}")
    
    return True


async def run_all_tests():
    """Run all integration tests"""
    
    logger.info("🚀 Starting XAgent integration tests...")
    
    tests = [
        test_basic_imports,
        test_agent_factory,
        test_tool_adapter,
        test_agent_interface,
        test_environment_variables
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if await test():
                passed += 1
                logger.info(f"✅ {test.__name__} passed")
            else:
                logger.error(f"❌ {test.__name__} failed")
        except Exception as e:
            logger.error(f"❌ {test.__name__} failed with exception: {e}")
    
    logger.info(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! XAgent integration is working correctly.")
        return True
    else:
        logger.error("💥 Some tests failed. Please check the errors above.")
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
