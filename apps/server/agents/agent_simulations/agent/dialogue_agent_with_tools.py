import logging
from typing import List, Optional

from langchain.schema import AIMessage, SystemMessage
from langchain_community.chat_models import ChatOpenAI

logger = logging.getLogger(__name__)

from agents.agent_simulations.agent.dialogue_agent import DialogueAgent
from agents.conversational.output_parser import ConvoOutputParser
from agents.xagent import AgentFactory, AgentInterface
from config import Config
from memory.zep.zep_memory import ZepMemory
from services.run_log import RunLogsManager
from typings.agent import AgentWithConfigsOutput


class DialogueAgentWithTools(DialogueAgent):
    def __init__(
        self,
        name: str,
        agent_with_configs: AgentWithConfigsOutput,
        system_message: SystemMessage,
        model: ChatOpenAI,
        tools: List[any],
        session_id: str,
        sender_name: str,
        is_memory: bool = False,
        run_logs_manager: Optional[RunLogsManager] = None,
        **tool_kwargs,
    ) -> None:
        super().__init__(name, agent_with_configs, system_message, model)
        self.tools = tools
        self.session_id = session_id
        self.sender_name = sender_name
        self.is_memory = is_memory
        self.run_logs_manager = run_logs_manager
        
        # Initialize agent factory for XAgent/ReAct switching
        self.agent_factory = AgentFactory()

    def send(self) -> str:
        """
        Applies the chatmodel to the message history
        and returns the message string
        """

        memory: ZepMemory

        # FIXME: This is a hack to get the memory working
        # if self.is_memory:
        memory = ZepMemory(
            session_id=self.session_id,
            url=Config.ZEP_API_URL,
            api_key=Config.ZEP_API_KEY,
            memory_key="chat_history",
            return_messages=True,
        )

        memory.human_name = self.sender_name
        memory.ai_name = self.agent_with_configs.agent.name
        memory.auto_save = False
        # else:
        #     memory = ConversationBufferMemory(
        #         memory_key="chat_history", return_messages=True
        #     )

        # Build task string with tool context
        prompt = "\n".join(self.message_history + [self.prefix])
        
        # Create agent using factory (XAgent or ReAct based on feature flags)
        agent: AgentInterface = self.agent_factory.create_agent(
            agent_type="dialogue",
            tools=self.tools,
            llm=self.model,
            memory=memory,
            run_logs_manager=self.run_logs_manager,
            system_message=self.system_message.content,
            output_parser=ConvoOutputParser()
        )
        
        # Execute task
        import asyncio
        try:
            # Try to run asynchronously first
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're already in an event loop, create a new one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(agent.run(prompt))
                    res = result.final_answer
                finally:
                    loop.close()
            else:
                result = loop.run_until_complete(agent.run(prompt))
                res = result.final_answer
        except Exception as e:
            # Fallback to synchronous execution if async fails
            logger.warning(f"Async execution failed, falling back to sync: {e}")
            result = agent.run(prompt)
            res = result.final_answer if hasattr(result, 'final_answer') else str(result)

        # FIXME: is memory
        # memory.save_ai_message(res)

        message = AIMessage(content=res)

        return message.content
