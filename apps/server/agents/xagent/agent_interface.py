"""
Abstract interface for both ReAct and XAgent implementations.
This maintains backward compatibility while enabling XAgent integration.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, AsyncGenerator
from dataclasses import dataclass


@dataclass
class AgentResult:
    """Standardized result format for both ReAct and XAgent"""
    final_answer: str
    tool_calls: List[Dict[str, Any]]
    running_records: Optional[Dict[str, Any]] = None
    memory_updates: Optional[Dict[str, Any]] = None
    voice_url: Optional[str] = None


class AgentInterface(ABC):
    """Abstract interface for both ReAct and XAgent implementations"""
    
    @abstractmethod
    async def run(
        self,
        task: str,
        files: Optional[List[str]] = None,
        history: Optional[List[Dict]] = None,
        **kwargs
    ) -> AgentResult:
        """Execute a task and return the result"""
        pass
    
    @abstractmethod
    async def stream_run(
        self,
        task: str,
        files: Optional[List[str]] = None,
        history: Optional[List[Dict]] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Execute a task and stream the results"""
        pass
    
    @abstractmethod
    def get_tool_descriptions(self) -> List[str]:
        """Get descriptions of available tools for prompt context"""
        pass
