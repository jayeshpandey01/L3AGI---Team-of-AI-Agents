# L3AGI XAgent Integration

This document provides comprehensive instructions for integrating XAgent into the L3AGI multi-agent framework, replacing the existing LangChain ReAct agents with XAgent's enhanced planner-actor-tool architecture.

## 🚀 Quick Start

### Prerequisites
- Python 3.10+ (XAgent requirement)
- Docker and Docker Compose
- Git (for submodule management)

### 1. Setup XAgent Integration

#### Linux/macOS
```bash
# Make setup script executable
chmod +x setup-xagent.sh

# Run setup script
./setup-xagent.sh
```

#### Windows
```powershell
# Run PowerShell setup script
.\setup-xagent.ps1

# If you encounter execution policy issues:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 2. Configure Environment
```bash
# Copy environment template
cp env.xagent.example .env.xagent

# Edit .env.xagent with your API keys
nano .env.xagent  # or use your preferred editor
```

### 3. Start XAgent Services
```bash
# Linux/macOS
./start-xagent.sh

# Windows
.\start-xagent.ps1
```

### 4. Verify Services
```bash
# Linux/macOS
./check-xagent-health.sh

# Windows
.\check-xagent-health.ps1
```

## 📁 Directory Structure

```
team-of-ai-agents/
├── third_party/xagent/          # XAgent submodule
├── configs/xagent/              # L3AGI-specific XAgent configuration
│   └── config.yml               # Main XAgent config
├── docker-compose.xagent.yml    # XAgent services orchestration
├── requirements-xagent.txt      # XAgent dependencies
├── env.xagent.example          # Environment template
├── setup-xagent.sh             # Linux/macOS setup script
├── setup-xagent.ps1            # Windows setup script
├── start-xagent.sh             # Service startup script
├── stop-xagent.sh              # Service stop script
├── check-xagent-health.sh      # Health check script
├── local_workspace/            # XAgent workspace directory
└── logs/xagent/                # XAgent logs and records
```

## 🔧 Configuration

### XAgent Configuration (`configs/xagent/config.yml`)

The configuration file is customized for L3AGI integration:

```yaml
# L3AGI-specific configuration
l3agi_integration:
  enabled: true
  memory_backend: zep
  zep_url: ${ZEP_API_URL}
  zep_api_key: ${ZEP_API_KEY}
  
  # Tool mapping configuration
  tool_adapters:
    - name: l3agi_tools
      enabled: true
      adapter_class: L3AGIToolAdapter
    
  # Memory integration
  memory:
    type: zep
    session_key: "chat_history"
    human_name: "Human"
    ai_name: "AI"
    
  # Telemetry integration
  telemetry:
    enabled: true
    run_logs_manager: true
    callback_handlers: true
```

### Environment Variables (`.env.xagent`)

Key configuration variables:

```bash
# XAgent Configuration
CONFIG_FILE=./configs/xagent/config.yml
XAGENT_ENABLED=true

# ToolServer Configuration
TOOLSERVER_URL=http://localhost:8080
TOOLSERVER_API_KEY=your_toolserver_key

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# L3AGI Integration
L3AGI_API_KEY=your_l3agi_api_key_here
ZEP_API_URL=http://localhost:8000
ZEP_API_KEY=your_zep_api_key_here

# Feature Flags
USE_XAGENT=true
FALLBACK_TO_REACT=true
```

## 🐳 Docker Services

The integration includes several Docker services:

### Core Services
- **ToolServerManager** (Port 8080): Manages tool execution and sandboxing
- **ToolServerNode**: Executes individual tools
- **XAgentServer** (Port 8090): Main XAgent API server
- **XAgent Web UI** (Port 5173): Web interface for XAgent

### Supporting Services
- **MongoDB**: ToolServer metadata storage
- **MySQL**: XAgent data storage
- **Redis**: XAgent caching and session management

### L3AGI Integration
- **l3agi-xagent-bridge**: Optional bridge service for L3AGI integration

## 🛠️ Tool Integration

### L3AGI → XAgent Tool Mapping

All 26 L3AGI toolkits are mapped to XAgent ToolServer capabilities:

| L3AGI Tool Category | XAgent ToolServer | Mapping Strategy |
|---------------------|-------------------|------------------|
| **Search Tools** | `web_search` | Direct mapping |
| **Communication** | `rapidapi_*` | RapidAPI integration |
| **Database** | `database_*` | Direct mapping |
| **AI/ML** | `python_notebook` + `rapidapi_*` | Hybrid approach |
| **Productivity** | `rapidapi_*` | RapidAPI integration |

### Tool Adapter

The `L3AGIToolAdapter` class bridges L3AGI tools with XAgent ToolServer:

```python
class L3AGIToolAdapter:
    """Bridges L3AGI's existing tools with XAgent's ToolServer"""
    
    def adapt_tool_call(self, tool_name: str, tool_args: Dict) -> Dict:
        """Convert L3AGI tool call to XAgent ToolServer format"""
        # Tool mapping logic here
        pass
```

## 🔄 Migration Strategy

### Adapter Pattern (Recommended)

The integration uses an adapter pattern to maintain backward compatibility:

```python
class AgentInterface(ABC):
    """Abstract interface for both ReAct and XAgent implementations"""
    
    @abstractmethod
    async def run(self, task: str, **kwargs) -> AgentResult:
        pass

class XAgentAdapter(AgentInterface):
    """Adapter that makes XAgent compatible with L3AGI's AgentInterface"""
    pass

class LangchainReactAgent(AgentInterface):
    """Existing ReAct implementation"""
    pass
```

### Feature Flags

Control XAgent usage with environment variables:

```bash
USE_XAGENT=true              # Enable XAgent
XAGENT_TOOLS_ONLY=false      # Use XAgent tools only
HYBRID_MODE=true            # Allow both ReAct and XAgent
FALLBACK_TO_REACT=true      # Fallback to ReAct on failure
```

## 📊 Monitoring and Health Checks

### Health Check Endpoints
- **XAgent Server**: `http://localhost:8090/health`
- **ToolServer**: `http://localhost:8080/health`
- **Web UI**: `http://localhost:5173`

### Health Check Script
```bash
# Linux/macOS
./check-xagent-health.sh

# Windows
.\check-xagent-health.ps1
```

### Logs
```bash
# View all service logs
docker-compose -f docker-compose.xagent.yml logs -f

# View specific service logs
docker-compose -f docker-compose.xagent.yml logs -f XAgentServer
docker-compose -f docker-compose.xagent.yml logs -f ToolServerManager
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Docker Services Not Starting
```bash
# Check Docker status
docker info

# Check available ports
netstat -tulpn | grep :8080
netstat -tulpn | grep :8090
netstat -tulpn | grep :5173
```

#### 2. XAgent Configuration Issues
```bash
# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('configs/xagent/config.yml'))"

# Check environment variables
docker-compose -f docker-compose.xagent.yml config
```

#### 3. Tool Execution Failures
```bash
# Check ToolServer logs
docker-compose -f docker-compose.xagent.yml logs ToolServerManager

# Verify tool configurations
curl http://localhost:8080/tools
```

#### 4. Memory Integration Issues
```bash
# Check Zep service
curl http://localhost:8000/health

# Verify Zep configuration in .env.xagent
grep ZEP .env.xagent
```

### Reset and Recovery

#### Complete Reset
```bash
# Stop all services
docker-compose -f docker-compose.xagent.yml down -v

# Remove all containers and volumes
docker-compose -f docker-compose.xagent.yml down --volumes --remove-orphans

# Rebuild and restart
docker-compose -f docker-compose.xagent.yml up --build -d
```

#### Fallback to ReAct
```bash
# Set environment variable
export USE_XAGENT=false

# Restart L3AGI services
# (This will use existing ReAct agents)
```

## 🔒 Security Considerations

### ToolServer Sandboxing
- All tools execute in isolated Docker containers
- File system access restricted to `/workspace` and `/tmp`
- Network access controlled and monitored

### API Key Management
- Store sensitive keys in `.env.xagent` (not committed to git)
- Use environment variables for configuration
- Implement key rotation and monitoring

### Access Control
- ToolServer requires API key authentication
- XAgent API protected with authentication
- Database access restricted to service containers

## 📈 Performance and Scaling

### Resource Requirements
- **Minimum**: 4GB RAM, 2 CPU cores
- **Recommended**: 8GB RAM, 4 CPU cores
- **Production**: 16GB+ RAM, 8+ CPU cores

### Scaling Options
```bash
# Scale ToolServer nodes
docker-compose -f docker-compose.xagent.yml up -d --scale ToolServerNode=3

# Scale XAgent workers
docker-compose -f docker-compose.xagent.yml up -d --scale XAgentServer=2
```

### Performance Monitoring
```bash
# Monitor resource usage
docker stats

# Check service performance
docker-compose -f docker-compose.xagent.yml exec XAgentServer top
```

## 🔮 Future Enhancements

### Planned Features
- **Multi-Agent Collaboration**: Enable multiple XAgent instances
- **Advanced Planning**: Enhanced milestone tracking and optimization
- **Tool Chaining**: Automatic tool composition and orchestration
- **Performance Analytics**: Detailed execution metrics and optimization

### Integration Roadmap
1. **Phase 1**: Basic XAgent integration (Current)
2. **Phase 2**: Advanced tool orchestration
3. **Phase 3**: Multi-agent collaboration
4. **Phase 4**: AI-powered optimization

## 📚 Additional Resources

### Documentation
- [XAgent Official Documentation](https://github.com/OpenBMB/XAgent)
- [ToolServer Documentation](https://github.com/OpenBMB/ToolServer)
- [L3AGI Documentation](https://github.com/l3vels/team-of-ai-agents)

### Support
- **Issues**: [L3AGI GitHub Issues](https://github.com/l3vels/team-of-ai-agents/issues)
- **Discussions**: [L3AGI GitHub Discussions](https://github.com/l3vels/team-of-ai-agents/discussions)
- **XAgent Issues**: [XAgent GitHub Issues](https://github.com/OpenBMB/XAgent/issues)

### Community
- Join the L3AGI community for updates and support
- Contribute to the XAgent integration
- Share your use cases and feedback

## 📄 License

This integration follows the same license as the L3AGI project. XAgent is licensed under the Apache 2.0 License.

---

**Note**: This integration is actively maintained and updated. For the latest information, always check the repository and documentation.
