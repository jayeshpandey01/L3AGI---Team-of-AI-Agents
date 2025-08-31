import asyncio
import logging

from agents.base_agent import BaseAgent
from agents.conversational.output_parser import ConvoOutputParser
from agents.conversational.streaming_aiter import AsyncCallbackHandler
from agents.handle_agent_errors import handle_agent_error
from agents.xagent import AgentFactory, AgentInterface
from config import Config
from memory.zep.zep_memory import ZepMemory
from postgres import PostgresChatMessageHistory
from services.pubsub import ChatPubSubService
from services.run_log import RunLogsManager
from services.voice import speech_to_text, text_to_speech
from typings.agent import AgentWithConfigsOutput
from typings.config import AccountSettings, AccountVoiceSettings
from utils.model import get_llm
from utils.system_message import SystemMessageBuilder

logger = logging.getLogger(__name__)


class ConversationalAgent(BaseAgent):
    async def run(
        self,
        settings: AccountSettings,
        voice_settings: AccountVoiceSettings,
        chat_pubsub_service: ChatPubSubService,
        agent_with_configs: AgentWithConfigsOutput,
        tools,
        prompt: str,
        voice_url: str,
        history: PostgresChatMessageHistory,
        human_message_id: str,
        run_logs_manager: RunLogsManager,
        pre_retrieved_context: str,
    ):
        memory = ZepMemory(
            session_id=str(self.session_id),
            url=Config.ZEP_API_URL,
            api_key=Config.ZEP_API_KEY,
            memory_key="chat_history",
            return_messages=True,
        )

        memory.human_name = self.sender_name
        memory.ai_name = agent_with_configs.agent.name

        system_message = SystemMessageBuilder(
            agent_with_configs, pre_retrieved_context
        ).build()

        res: str

        try:
            if voice_url:
                configs = agent_with_configs.configs
                prompt = speech_to_text(voice_url, configs, voice_settings)

            llm = get_llm(
                settings,
                agent_with_configs,
            )

            streaming_handler = AsyncCallbackHandler()

            llm.streaming = True
            # llm.callbacks = [
            #     run_logs_manager.get_agent_callback_handler(),
            #     streaming_handler,
            # ]

            # Create agent using factory (XAgent or ReAct based on feature flags)
            agent_factory = AgentFactory()
            agent: AgentInterface = agent_factory.create_agent(
                agent_type="conversational",
                tools=tools,
                llm=llm,
                memory=memory,
                run_logs_manager=run_logs_manager,
                system_message=system_message,
                voice_settings=voice_settings
            )

            # Execute task using the agent adapter
            chunks = []
            final_answer_detected = False
            
            try:
                async for chunk in agent.stream_run(prompt):
                    if chunk:
                        chunks.append(chunk)
                        yield chunk
                
                # Combine chunks for final response
                res = "".join(chunks)
                
            except Exception as e:
                logger.error(f"Agent streaming execution failed: {e}")
                res = f"Error during execution: {str(e)}"
                yield res

        except Exception as err:
            res = handle_agent_error(err)

            memory.save_context(
                {
                    "input": prompt,
                    "chat_history": memory.load_memory_variables({})["chat_history"],
                },
                {
                    "output": res,
                },
            )

            yield res

        try:
            configs = agent_with_configs.configs
            voice_url = None
            if "Voice" in configs.response_mode:
                voice_url = text_to_speech(res, configs, voice_settings)
                pass
        except Exception as err:
            res = f"{res}\n\n{handle_agent_error(err)}"

            yield res

        ai_message = history.create_ai_message(
            res,
            human_message_id,
            agent_with_configs.agent.id,
            voice_url,
        )

        chat_pubsub_service.send_chat_message(chat_message=ai_message)
