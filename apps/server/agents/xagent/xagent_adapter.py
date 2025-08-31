"""
XAgent adapter that implements the AgentInterface.
This makes XAgent compatible with L3AGI's existing agent system.
"""

import os
import asyncio
import aiohttp
from typing import List, Optional, Dict, Any, AsyncGenerator
import json
import logging

from .agent_interface import AgentInterface, AgentResult
from .tool_adapter import L3AGIToolAdapter
from memory.zep.zep_memory import ZepMemory
from services.run_log import RunLogsManager

logger = logging.getLogger(__name__)


class XAgentAdapter(AgentInterface):
    """Adapter that makes XAgent compatible with L3AGI's AgentInterface"""
    
    def __init__(
        self,
        config_path: str,
        memory: ZepMemory,
        run_logs_manager: RunLogsManager,
        tools: List[Any],
        voice_settings: Optional[Dict] = None
    ):
        self.config_path = config_path
        self.memory = memory
        self.run_logs_manager = run_logs_manager
        self.tools = tools
        self.voice_settings = voice_settings
        
        # Initialize XAgent components
        self.xagent_url = os.getenv("XAGENT_URL", "http://localhost:8090")
        self.toolserver_url = os.getenv("TOOLSERVER_URL", "http://localhost:8080")
        self.tool_adapter = L3AGIToolAdapter()
        
        # Tool descriptions for prompt context
        self._tool_descriptions = self._build_tool_descriptions()
    
    def _build_tool_descriptions(self) -> List[str]:
        """Build tool descriptions for prompt context"""
        descriptions = []
        for tool in self.tools:
            if hasattr(tool, 'description'):
                descriptions.append(f"- {tool.name}: {tool.description}")
            elif hasattr(tool, 'name'):
                descriptions.append(f"- {tool.name}: Available tool")
        return descriptions
    
    def get_tool_descriptions(self) -> List[str]:
        """Get descriptions of available tools for prompt context"""
        return self._tool_descriptions
    
    async def run(
        self,
        task: str,
        files: Optional[List[str]] = None,
        history: Optional[List[Dict]] = None,
        **kwargs
    ) -> AgentResult:
        """Execute a task via XAgent and return the result"""
        
        try:
            # Convert L3AGI inputs to XAgent format
            xagent_input = self._convert_input(task, files, history, kwargs)
            
            # Execute via XAgent API
            xagent_result = await self._call_xagent_api(xagent_input)
            
            # Convert XAgent result back to L3AGI format
            return self._convert_output(xagent_result)
            
        except Exception as e:
            logger.error(f"XAgent execution failed: {e}")
            # Return error result that can be handled by caller
            return AgentResult(
                final_answer=f"Error: {str(e)}",
                tool_calls=[],
                running_records={"error": str(e)}
            )
    
    async def stream_run(
        self,
        task: str,
        files: Optional[List[str]] = None,
        history: Optional[List[Dict]] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Execute a task via XAgent and stream the results"""
        
        try:
            # Convert L3AGI inputs to XAgent format
            xagent_input = self._convert_input(task, files, history, kwargs)
            
            # Execute via XAgent streaming API
            async for chunk in self._call_xagent_streaming_api(xagent_input):
                yield chunk
                
        except Exception as e:
            logger.error(f"XAgent streaming execution failed: {e}")
            yield f"Error: {str(e)}"
    
    def _convert_input(
        self,
        task: str,
        files: Optional[List[str]] = None,
        history: Optional[List[Dict]] = None,
        kwargs: Dict = None
    ) -> Dict[str, Any]:
        """Convert L3AGI inputs to XAgent format"""
        
        # Build task description with tool context
        tool_context = "\n".join(self._tool_descriptions) if self._tool_descriptions else ""
        
        if tool_context:
            enhanced_task = f"{task}\n\nAvailable tools:\n{tool_context}"
        else:
            enhanced_task = task
        
        # Convert chat history to XAgent format
        xagent_history = []
        if history:
            for msg in history:
                if isinstance(msg, dict):
                    if msg.get('type') == 'human':
                        xagent_history.append({
                            "role": "user",
                            "content": msg.get('content', '')
                        })
                    elif msg.get('type') == 'ai':
                        xagent_history.append({
                            "role": "assistant", 
                            "content": msg.get('content', '')
                        })
        
        result = {
            "task": enhanced_task,
            "files": files or [],
            "history": xagent_history,
            "config_path": self.config_path,
            "memory_session_id": str(self.memory.session_id) if self.memory else None,
            "voice_enabled": bool(self.voice_settings)
        }
        
        if kwargs:
            result.update(kwargs)
            
        return result
    
    async def _call_xagent_api(self, xagent_input: Dict) -> Dict:
        """Call XAgent API synchronously"""
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.xagent_url}/run",
                json=xagent_input,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"XAgent API error {response.status}: {error_text}")
    
    async def _call_xagent_streaming_api(self, xagent_input: Dict) -> AsyncGenerator[str, None]:
        """Call XAgent streaming API"""
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.xagent_url}/stream_run",
                json=xagent_input,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    async for line in response.content:
                        if line:
                            try:
                                chunk_data = json.loads(line.decode().strip())
                                if 'content' in chunk_data:
                                    yield chunk_data['content']
                            except json.JSONDecodeError:
                                # Handle non-JSON chunks
                                yield line.decode()
                else:
                    error_text = await response.text()
                    raise Exception(f"XAgent streaming API error {response.status}: {error_text}")
    
    def _convert_output(self, xagent_result: Dict) -> AgentResult:
        """Convert XAgent result back to L3AGI format"""
        
        # Extract final answer
        final_answer = xagent_result.get('final_answer', '')
        if not final_answer:
            # Try alternative fields
            final_answer = (
                xagent_result.get('result', '') or 
                xagent_result.get('output', '') or 
                xagent_result.get('response', '') or
                'No answer provided'
            )
        
        # Extract tool calls
        tool_calls = xagent_result.get('tool_calls', [])
        
        # Extract running records
        running_records = xagent_result.get('running_records', {})
        
        # Extract memory updates
        memory_updates = xagent_result.get('memory_updates', {})
        
        # Extract voice URL if available
        voice_url = xagent_result.get('voice_url')
        
        return AgentResult(
            final_answer=final_answer,
            tool_calls=tool_calls,
            running_records=running_records,
            memory_updates=memory_updates,
            voice_url=voice_url
        )
    
    async def health_check(self) -> bool:
        """Check if XAgent is healthy"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.xagent_url}/health") as response:
                    return response.status == 200
        except Exception:
            return False
