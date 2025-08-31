"""
Agent factory that creates either ReAct or XAgent implementations based on feature flags.
This enables seamless switching between agent types.
"""

import os
from typing import List, Optional, Dict, Any
import logging

from .agent_interface import AgentInterface
from .react_agent_adapter import LangchainReactAgent
from .xagent_adapter import XAgentAdapter
from memory.zep.zep_memory import ZepMemory
from services.run_log import RunLogsManager

logger = logging.getLogger(__name__)


class AgentFactory:
    """Factory for creating agents with fallback capability"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.use_xagent = self._get_feature_flag("USE_XAGENT", False)
        self.fallback_to_react = self._get_feature_flag("FALLBACK_TO_REACT", True)
        self.hybrid_mode = self._get_feature_flag("HYBRID_MODE", False)
        
        logger.info(f"AgentFactory initialized: use_xagent={self.use_xagent}, "
                   f"fallback_to_react={self.fallback_to_react}, hybrid_mode={self.hybrid_mode}")
    
    def _get_feature_flag(self, flag_name: str, default: bool) -> bool:
        """Get feature flag value from environment or config"""
        # Check environment variable first
        env_value = os.getenv(flag_name)
        if env_value is not None:
            return env_value.lower() == "true"
        
        # Check config dict
        config_value = self.config.get(flag_name)
        if config_value is not None:
            return bool(config_value)
        
        return default
    
    def create_agent(
        self,
        agent_type: str,
        tools: List[Any],
        llm: Any,
        memory: ZepMemory,
        run_logs_manager: Optional[RunLogsManager] = None,
        system_message: Optional[str] = None,
        **kwargs
    ) -> AgentInterface:
        """Create an agent based on configuration and feature flags"""
        
        try:
            if self.use_xagent:
                return self._create_xagent_agent(
                    tools, llm, memory, run_logs_manager, system_message, **kwargs
                )
            else:
                return self._create_react_agent(
                    tools, llm, memory, run_logs_manager, system_message, **kwargs
                )
                
        except Exception as e:
            if self.fallback_to_react:
                logger.warning(f"Failed to create XAgent, falling back to ReAct: {e}")
                return self._create_react_agent(
                    tools, llm, memory, run_logs_manager, system_message, **kwargs
                )
            else:
                raise
    
    def _create_xagent_agent(
        self,
        tools: List[Any],
        llm: Any,
        memory: ZepMemory,
        run_logs_manager: Optional[RunLogsManager],
        system_message: Optional[str],
        **kwargs
    ) -> XAgentAdapter:
        """Create an XAgent adapter"""
        
        config_path = os.getenv("XAGENT_CONFIG_PATH", "./configs/xagent/config.yml")
        
        # Extract voice settings if available
        voice_settings = kwargs.get("voice_settings")
        
        agent = XAgentAdapter(
            config_path=config_path,
            memory=memory,
            run_logs_manager=run_logs_manager,
            tools=tools,
            voice_settings=voice_settings
        )
        
        logger.info("Created XAgent adapter successfully")
        return agent
    
    def _create_react_agent(
        self,
        tools: List[Any],
        llm: Any,
        memory: ZepMemory,
        run_logs_manager: Optional[RunLogsManager],
        system_message: Optional[str],
        **kwargs
    ) -> LangchainReactAgent:
        """Create a ReAct agent adapter"""
        
        agent = LangchainReactAgent(
            tools=tools,
            llm=llm,
            memory=memory,
            run_logs_manager=run_logs_manager,
            system_message=system_message,
            **kwargs
        )
        
        logger.info("Created ReAct agent adapter successfully")
        return agent
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get information about the current agent configuration"""
        return {
            "use_xagent": self.use_xagent,
            "fallback_to_react": self.fallback_to_react,
            "hybrid_mode": self.hybrid_mode,
            "agent_type": "xagent" if self.use_xagent else "react"
        }
    
    def switch_to_xagent(self):
        """Switch to XAgent implementation"""
        self.use_xagent = True
        logger.info("Switched to XAgent implementation")
    
    def switch_to_react(self):
        """Switch to ReAct implementation"""
        self.use_xagent = False
        logger.info("Switched to ReAct implementation")
    
    def toggle_agent_type(self):
        """Toggle between XAgent and ReAct implementations"""
        self.use_xagent = not self.use_xagent
        agent_type = "XAgent" if self.use_xagent else "ReAct"
        logger.info(f"Toggled to {agent_type} implementation")
    
    def is_xagent_available(self) -> bool:
        """Check if XAgent is available and healthy"""
        if not self.use_xagent:
            return False
        
        try:
            # Try to create a test XAgent adapter
            test_agent = XAgentAdapter(
                config_path="./configs/xagent/config.yml",
                memory=ZepMemory(session_id="test", url="http://localhost:8000", api_key="test"),
                run_logs_manager=None,
                tools=[]
            )
            
            # Check health
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                is_healthy = loop.run_until_complete(test_agent.health_check())
                return is_healthy
            finally:
                loop.close()
                
        except Exception as e:
            logger.warning(f"XAgent health check failed: {e}")
            return False
    
    def get_recommended_agent_type(self) -> str:
        """Get the recommended agent type based on availability and configuration"""
        if self.use_xagent and self.is_xagent_available():
            return "xagent"
        else:
            return "react"
