"""
ReAct agent adapter that implements the AgentInterface.
This wraps the existing LangChain ReAct implementation for backward compatibility.
"""

import asyncio
from typing import List, Optional, Dict, Any, AsyncGenerator
import logging

from langchain.agents import AgentType, initialize_agent, create_react_agent
from langchain.agents import AgentExecutor
from langchain import hub
from langchain.schema import AIMessage

from .agent_interface import AgentInterface, AgentResult
from agents.conversational.output_parser import ConvoOutputParser
from memory.zep.zep_memory import ZepMemory
from services.run_log import RunLogsManager

logger = logging.getLogger(__name__)


class LangchainReactAgent(AgentInterface):
    """Adapter that wraps existing LangChain ReAct implementation"""
    
    def __init__(
        self,
        tools: List[Any],
        llm: Any,
        memory: ZepMemory,
        run_logs_manager: Optional[RunLogsManager] = None,
        system_message: Optional[str] = None,
        **kwargs
    ):
        self.tools = tools
        self.llm = llm
        self.memory = memory
        self.run_logs_manager = run_logs_manager
        self.system_message = system_message
        self.kwargs = kwargs
        
        # Build tool descriptions for prompt context
        self._tool_descriptions = self._build_tool_descriptions()
        
        # Initialize the ReAct agent
        self._agent = self._initialize_react_agent()
    
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
    
    def _initialize_react_agent(self):
        """Initialize the ReAct agent with the existing pattern"""
        
        # Use the same pattern as in conversational.py
        agent_prompt = hub.pull("hwchase17/react")
        
        agent = create_react_agent(
            self.llm, 
            self.tools, 
            prompt=agent_prompt
        )
        
        # Create executor with callbacks
        callbacks = []
        if self.run_logs_manager:
            callbacks.append(self.run_logs_manager.get_agent_callback_handler())
        
        executor = AgentExecutor(
            agent=agent, 
            tools=self.tools, 
            verbose=True,
            callbacks=callbacks,
            **self.kwargs
        )
        
        return executor
    
    async def run(
        self,
        task: str,
        files: Optional[List[str]] = None,
        history: Optional[List[Dict]] = None,
        **kwargs
    ) -> AgentResult:
        """Execute a task via ReAct agent and return the result"""
        
        try:
            # Build enhanced task with tool context
            tool_context = "\n".join(self._tool_descriptions) if self._tool_descriptions else ""
            
            if tool_context:
                enhanced_task = f"{task}\n\nAvailable tools:\n{tool_context}"
            else:
                enhanced_task = task
            
            # Execute via ReAct agent
            result = await asyncio.to_thread(
                self._agent.run,
                input=enhanced_task
            )
            
            # Convert to AgentResult format
            return AgentResult(
                final_answer=result,
                tool_calls=[],  # ReAct doesn't provide detailed tool call info
                running_records={"agent_type": "react", "result": result}
            )
            
        except Exception as e:
            logger.error(f"ReAct agent execution failed: {e}")
            return AgentResult(
                final_answer=f"Error: {str(e)}",
                tool_calls=[],
                running_records={"error": str(e), "agent_type": "react"}
            )
    
    async def stream_run(
        self,
        task: str,
        files: Optional[List[str]] = None,
        history: Optional[List[Dict]] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Execute a task via ReAct agent and stream the results"""
        
        try:
            # Build enhanced task with tool context
            tool_context = "\n".join(self._tool_descriptions) if self._tool_descriptions else ""
            
            if tool_context:
                enhanced_task = f"{task}\n\nAvailable tools:\n{tool_context}"
            else:
                enhanced_task = task
            
            # Execute via ReAct agent streaming
            chunks = []
            final_answer_detected = False
            
            async for event in self._agent.astream_events(
                {"input": enhanced_task}, version="v1"
            ):
                kind = event["event"]
                
                if kind == "on_chat_model_stream":
                    content = event["data"]["chunk"].content
                    if content:
                        chunks.append(content)
                        
                        # Check for final answer pattern (same as in conversational.py)
                        if (
                            len(chunks) >= 3
                            and chunks[-3].strip() == "Final"
                            and chunks[-2].strip() == "Answer"
                            and chunks[-1].strip() == ":"
                        ):
                            final_answer_detected = True
                            continue
                        
                        if final_answer_detected:
                            yield content
            
            # Extract final answer from chunks
            full_response = "".join(chunks)
            final_answer_index = full_response.find("Final Answer:")
            if final_answer_index != -1:
                start_index = final_answer_index + len("Final Answer:")
                final_answer = full_response[start_index:].lstrip()
            else:
                final_answer = "Final Answer not found in response."
            
            # Yield the final answer if not already yielded
            if not final_answer_detected:
                yield final_answer
                
        except Exception as e:
            logger.error(f"ReAct agent streaming execution failed: {e}")
            yield f"Error: {str(e)}"
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get information about the ReAct agent"""
        return {
            "agent_type": "react",
            "tools_count": len(self.tools),
            "tool_names": [getattr(tool, 'name', str(tool)) for tool in self.tools],
            "memory_type": "zep" if self.memory else "none",
            "system_message": self.system_message
        }
    
    def update_tools(self, new_tools: List[Any]):
        """Update the tools used by the agent"""
        self.tools = new_tools
        self._tool_descriptions = self._build_tool_descriptions()
        # Reinitialize agent with new tools
        self._agent = self._initialize_react_agent()
    
    def update_system_message(self, new_system_message: str):
        """Update the system message"""
        self.system_message = new_system_message
        # Reinitialize agent with new system message
        self._agent = self._initialize_react_agent()
