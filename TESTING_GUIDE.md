# XAgent Integration Testing Guide

This guide covers all aspects of testing the XAgent integration with L3AGI, from unit tests to end-to-end demonstrations.

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Docker and Docker Compose
- XAgent services running (see setup guide)

### Run All Tests
```bash
# Run all tests
python run_tests.py --all

# Check service health first
python run_tests.py --check-services
```

## 📋 Test Categories

### 1. Unit Tests (Fast, No External Dependencies)
**Purpose**: Test adapter functionality, mocks, and history mapping
**Duration**: 1-2 minutes
**Requirements**: Python only

```bash
# Run unit tests
python run_tests.py --unit

# Or directly with pytest
python -m pytest tests/unit/ -m unit -v
```

**What's Tested**:
- ✅ Adapter initialization and configuration
- ✅ Tool description building
- ✅ Input/output conversion
- ✅ Error handling and fallbacks
- ✅ History context preservation
- ✅ Mock-based scenarios

### 2. Integration Tests (Requires XAgent Services)
**Purpose**: Test real XAgent API calls and ToolServer integration
**Duration**: 5-10 minutes
**Requirements**: Docker, XAgent services running

```bash
# Start XAgent services first
docker-compose -f docker-compose.xagent.yml up -d

# Run integration tests
python run_tests.py --integration

# Or directly with pytest
python -m pytest tests/test_xagent_integration.py -m integration -v
```

**What's Tested**:
- ✅ XAgent service health checks
- ✅ Web search tasks (web browser tool)
- ✅ Coding tasks (Python notebook tool)
- ✅ File editing tasks (file editor tool)
- ✅ Streaming execution
- ✅ Running records creation
- ✅ Process exit verification

### 3. Specific Test Types

#### XAgent Functionality Tests
```bash
python run_tests.py --xagent
```

#### ReAct Compatibility Tests
```bash
python run_tests.py --react
```

#### Mock-Based Tests
```bash
python run_tests.py --mock
```

#### History Mapping Tests
```bash
python run_tests.py --history
```

## 🧪 Individual Test Files

### Unit Tests
- **`tests/unit/test_xagent_adapters.py`**: Core adapter functionality
  - `TestAgentInterface`: Abstract interface validation
  - `TestXAgentAdapter`: XAgent adapter with mocks
  - `TestLangchainReactAgent`: ReAct adapter with mocks
  - `TestL3AGIToolAdapter`: Tool mapping and adaptation
  - `TestAgentFactory`: Factory pattern and fallbacks
  - `TestHistoryMapping`: Context preservation

### Integration Tests
- **`tests/test_xagent_integration.py`**: Real service integration
  - `TestXAgentIntegration`: End-to-end workflows
  - `TestXAgentFallback`: Fallback mechanisms

### Legacy Tests
- **`apps/server/test.py`**: Updated for both ReAct and XAgent
  - Basic functionality testing
  - Streaming validation
  - Fallback verification

## 🔍 Test Details

### Unit Test Coverage

#### Adapter Functionality
```python
def test_xagent_adapter_initialization(self, xagent_adapter):
    """Test XAgent adapter initialization"""
    assert xagent_adapter is not None
    assert hasattr(xagent_adapter, 'run')
    assert hasattr(xagent_adapter, 'stream_run')
    assert hasattr(xagent_adapter, 'get_tool_descriptions')
```

#### Mock-Based Testing
```python
@patch.object(xagent_adapter, '_call_xagent_api', return_value=mock_response)
async def test_xagent_adapter_run_success(self, xagent_adapter):
    """Test successful XAgent execution"""
    result = await xagent_adapter.run("Test task")
    assert isinstance(result, AgentResult)
    assert result.final_answer == "Task completed successfully"
```

#### History Context Preservation
```python
def test_coherent_output_with_context(self, mock_memory):
    """Test that output remains coherent with context"""
    # Verify that passing 3-5 turns as context
    # leads to coherent output
    assert "Based on our conversation" in result.final_answer
    assert result.running_records["context_used"] is True
```

### Integration Test Coverage

#### Service Health Checks
```python
def test_xagent_services_health(self, xagent_services):
    """Test that XAgent services are healthy"""
    # XAgent Server health
    response = requests.get("http://localhost:8090/health")
    assert response.status_code == 200
    
    # ToolServer health
    response = requests.get("http://localhost:8080/health")
    assert response.status_code == 200
    
    # XAgent Web UI accessibility
    response = requests.get("http://localhost:5173")
    assert response.status_code == 200
```

#### Real Task Execution
```python
async def test_xagent_web_search_task(self, agent_factory, mock_components):
    """Test XAgent with web search task (uses web browser tool)"""
    task = "Search for the latest AI news and provide a summary"
    
    result = await agent.run(task)
    
    # Verify result structure
    assert result is not None
    assert hasattr(result, 'final_answer')
    assert isinstance(result.final_answer, str)
    assert len(result.final_answer) > 0
    
    # Verify running records
    assert hasattr(result, 'running_records')
    assert result.running_records is not None
```

#### Running Records Validation
```python
def test_running_records_creation(self, xagent_services):
    """Test that running records are created with steps"""
    records_dir = Path("./logs/xagent")
    
    if records_dir.exists():
        record_files = list(records_dir.glob("*.json"))
        
        if record_files:
            latest_record = max(record_files, key=lambda p: p.stat().st_mtime)
            
            with open(latest_record, 'r') as f:
                record_data = json.load(f)
            
            # Verify record structure
            assert "steps" in record_data or "actions" in record_data
            assert "task" in record_data
            assert "result" in record_data
```

## 🐛 Troubleshooting

### Common Issues

#### 1. Import Errors
```bash
# Ensure you're in the project root
cd team-of-ai-agents

# Add server directory to Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/apps/server"
```

#### 2. XAgent Services Not Running
```bash
# Check service status
python run_tests.py --check-services

# Start services
docker-compose -f docker-compose.xagent.yml up -d

# Wait for services to be ready
sleep 30
```

#### 3. Test Failures
```bash
# Run with verbose output
python -m pytest tests/ -v -s

# Run specific failing test
python -m pytest tests/unit/test_xagent_adapters.py::TestXAgentAdapter::test_xagent_adapter_run_success -v -s
```

#### 4. Mock Issues
```bash
# Ensure unittest.mock is available
python -c "from unittest.mock import Mock, patch; print('Mocks available')"

# Check Python version (3.10+ required)
python --version
```

### Debug Mode
```bash
# Run tests with debug output
python -m pytest tests/ -v -s --tb=long

# Run single test with debugger
python -m pytest tests/unit/test_xagent_adapters.py::TestXAgentAdapter::test_xagent_adapter_run_success -v -s --pdb
```

## 📊 Test Results

### Expected Output

#### Unit Tests
```
tests/unit/test_xagent_adapters.py::TestAgentInterface::test_agent_interface_abstract PASSED
tests/unit/test_xagent_adapters.py::TestAgentInterface::test_agent_result_structure PASSED
tests/unit/test_xagent_adapters.py::TestXAgentAdapter::test_xagent_adapter_initialization PASSED
...
✅ Unit Tests completed successfully!
```

#### Integration Tests
```
tests/test_xagent_integration.py::TestXAgentIntegration::test_xagent_services_health PASSED
tests/test_xagent_integration.py::TestXAgentIntegration::test_agent_factory_xagent_creation PASSED
tests/test_xagent_integration.py::TestXAgentIntegration::test_xagent_web_search_task PASSED
...
✅ Integration Tests completed successfully!
```

### Success Criteria
- ✅ All unit tests pass (100% pass rate)
- ✅ All integration tests pass (100% pass rate)
- ✅ Services remain responsive after tests
- ✅ Running records are created with proper structure
- ✅ No unhandled exceptions or crashes
- ✅ Clean process exit

## 🎯 Testing Strategy

### Phase 1: Unit Testing (Fast Feedback)
1. **Adapter Tests**: Verify interface compliance
2. **Mock Tests**: Test error scenarios and edge cases
3. **History Tests**: Validate context preservation
4. **Factory Tests**: Test fallback mechanisms

### Phase 2: Integration Testing (Real Services)
1. **Service Health**: Verify all services are running
2. **Task Execution**: Test real XAgent workflows
3. **Tool Integration**: Validate ToolServer functionality
4. **Record Creation**: Check running_records generation

### Phase 3: End-to-End Validation
1. **Complete Workflows**: Full task execution
2. **Performance**: Response time validation
3. **Reliability**: Long-running stability tests
4. **User Experience**: Verify coherent outputs

## 🔄 Continuous Testing

### Pre-commit Hooks
```bash
# Run unit tests before commit
python run_tests.py --unit

# Run quick integration check
python run_tests.py --check-services
```

### CI/CD Integration
```yaml
# Example GitHub Actions workflow
- name: Run Unit Tests
  run: python run_tests.py --unit

- name: Run Integration Tests
  run: |
    docker-compose -f docker-compose.xagent.yml up -d
    sleep 30
    python run_tests.py --integration
```

### Monitoring
```bash
# Check test coverage
python -m pytest tests/ --cov=agents.xagent --cov-report=html

# Run performance benchmarks
python -m pytest tests/ -m slow --durations=10
```

## 📚 Additional Resources

### Test Configuration
- **`pytest.ini`**: Pytest configuration and markers
- **`run_tests.py`**: Test runner script with options
- **`TESTING_GUIDE.md`**: This comprehensive guide

### Related Documentation
- **`XAGENT_INTEGRATION_README.md`**: Setup and usage guide
- **`XAGENT_IMPLEMENTATION_SUMMARY.md`**: Implementation details
- **`docker-compose.xagent.yml`**: Service orchestration

### Support
- Check service logs: `docker-compose -f docker-compose.xagent.yml logs`
- Verify environment: `python run_tests.py --check-services`
- Run diagnostics: `python run_tests.py --summary`

---

**Next Steps**: After running tests successfully, proceed to the E2E demo phase to capture screenshots for submission.
