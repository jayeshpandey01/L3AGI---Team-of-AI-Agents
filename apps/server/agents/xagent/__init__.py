"""
XAgent integration package for L3AGI.
This package provides adapters to integrate XAgent with L3AGI's existing agent system.
"""

from .agent_interface import AgentInterface, AgentResult
from .xagent_adapter import XAgentAdapter
from .react_agent_adapter import LangchainReactAgent
from .tool_adapter import L3AGIToolAdapter
from .agent_factory import AgentFactory

__all__ = [
    "AgentInterface",
    "AgentResult", 
    "XAgentAdapter",
    "LangchainReactAgent",
    "L3AGIToolAdapter",
    "AgentFactory"
]

__version__ = "1.0.0"
