# L3AGI ReAct Inventory - Executive Summary

## Key Findings

### 1. ReAct Usage Locations
- **3 active implementations** found in the codebase
- **2 patterns** of ReAct agent construction:
  - Legacy: `initialize_agent` with `AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION`
  - Current: `create_react_agent` with `hub.pull("hwchase17/react")`

### 2. Core Files to Migrate
```
apps/server/agents/conversational/conversational.py     # Main conversational agent
apps/server/agents/agent_simulations/agent/dialogue_agent_with_tools.py  # Dialogue agent
apps/server/test.py                                    # Test implementation
```

### 3. Tool System
- **26 toolkits** with 50+ individual tools
- **Custom BaseTool** extending LangChain's BaseTool
- **Toolkit-based organization** with environment configuration
- **Account-scoped** tool configuration

### 4. Memory System
- **ZepMemory** extending ConversationBufferMemory
- **Session-based** persistence
- **Chat history** integration with key "chat_history"

### 5. Telemetry
- **RunLogsManager** for comprehensive tracking
- **Callback handlers** for agent, tool, and LLM monitoring
- **Session correlation** and user tracking

### 6. Input/Output Contract
- **Input**: User prompt, chat history, tools, system message, voice settings
- **Output**: Final reply, streaming chunks, tool calls, memory updates, voice
- **State**: Session, tool, memory, and run state management

## Migration Priority
1. **High**: conversational.py (main agent)
2. **Medium**: dialogue_agent_with_tools.py (simulation agent)  
3. **Low**: test.py (test implementation)

## Critical Dependencies to Preserve
- All 26 toolkits must remain functional
- ZepMemory integration
- Streaming response handling
- Voice input/output support
- Run logs telemetry
- Account/agent configuration system
