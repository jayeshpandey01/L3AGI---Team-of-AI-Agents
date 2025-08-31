#!/usr/bin/env python3
"""
End-to-End Demo Script for XAgent Integration
This script runs a real L3AGI task through XAgent to demonstrate functionality.
Use this to capture screenshots for submission.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Add the server directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'apps', 'server'))

from unittest.mock import Mock
from agents.xagent import AgentFactory, AgentInterface
from memory.zep.zep_memory import ZepMemory
from services.run_log import RunLogsManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class E2EDemo:
    """End-to-End demonstration of XAgent integration"""
    
    def __init__(self):
        self.agent_factory = AgentFactory()
        self.agent_factory.use_xagent = True
        
        # Create mock components for demo
        self.tools = [
            Mock(name="web_search", description="Search the web for information"),
            Mock(name="file_editor", description="Edit files on the system"),
            Mock(name="python_notebook", description="Execute Python code"),
            Mock(name="web_browser", description="Browse and scrape web pages")
        ]
        
        self.memory = ZepMemory(
            session_id="e2e_demo_session",
            url="http://localhost:8000",
            api_key="demo_key"
        )
        
        self.run_logs_manager = None
    
    async def run_demo_task(self, task_description: str) -> str:
        """Run a demo task and return the result"""
        logger.info(f"🚀 Starting E2E demo task: {task_description}")
        
        try:
            # Create agent
            agent = self.agent_factory.create_agent(
                agent_type="e2e_demo",
                tools=self.tools,
                llm=Mock(),
                memory=self.memory,
                run_logs_manager=self.run_logs_manager
            )
            
            logger.info(f"✅ Agent created: {type(agent).__name__}")
            
            # Execute task
            logger.info("🔄 Executing task...")
            result = await agent.run(task_description)
            
            logger.info("✅ Task completed successfully!")
            logger.info(f"📝 Final Answer: {result.final_answer[:200]}...")
            
            if result.running_records:
                logger.info(f"📊 Running Records: {len(result.running_records)} entries")
            
            return result.final_answer
            
        except Exception as e:
            logger.error(f"❌ Task execution failed: {e}")
            return f"Error: {str(e)}"
    
    async def run_streaming_demo(self, task_description: str):
        """Run a streaming demo task"""
        logger.info(f"🚀 Starting streaming E2E demo: {task_description}")
        
        try:
            # Create agent
            agent = self.agent_factory.create_agent(
                agent_type="e2e_demo",
                tools=self.tools,
                llm=Mock(),
                memory=self.memory,
                run_logs_manager=self.run_logs_manager
            )
            
            logger.info(f"✅ Agent created: {type(agent).__name__}")
            
            # Execute streaming task
            logger.info("🔄 Executing streaming task...")
            chunks = []
            
            async for chunk in agent.stream_run(task_description):
                if chunk:
                    chunks.append(chunk)
                    print(f"📡 Chunk: {chunk}")
            
            full_response = "".join(chunks)
            logger.info(f"✅ Streaming completed: {len(chunks)} chunks received")
            logger.info(f"📝 Full Response: {full_response[:200]}...")
            
            return full_response
            
        except Exception as e:
            logger.error(f"❌ Streaming task failed: {e}")
            return f"Error: {str(e)}"
    
    def check_services(self):
        """Check if required services are running"""
        logger.info("🔍 Checking service health...")
        
        import requests
        
        services = [
            ("XAgent Server", "http://localhost:8090/health"),
            ("ToolServer", "http://localhost:8080/health"),
            ("XAgent Web UI", "http://localhost:5173")
        ]
        
        all_healthy = True
        
        for service_name, url in services:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    logger.info(f"✅ {service_name}: Healthy")
                else:
                    logger.warning(f"⚠️  {service_name}: Status {response.status_code}")
                    all_healthy = False
            except requests.exceptions.RequestException:
                logger.error(f"❌ {service_name}: Not accessible")
                all_healthy = False
        
        return all_healthy
    
    def show_demo_menu(self):
        """Show available demo tasks"""
        print("\n🎯 XAgent E2E Demo - Available Tasks")
        print("=" * 50)
        print("1. Web Search Task")
        print("   - Search for latest AI news and summarize")
        print("   - Demonstrates web browser tool")
        print()
        print("2. Coding Task")
        print("   - Write a Python function to calculate factorial")
        print("   - Demonstrates Python notebook tool")
        print()
        print("3. File Editing Task")
        print("   - Create and edit a text file")
        print("   - Demonstrates file editor tool")
        print()
        print("4. Streaming Task")
        print("   - Explain machine learning concepts with streaming")
        print("   - Demonstrates real-time response generation")
        print()
        print("5. Custom Task")
        print("   - Enter your own task description")
        print()
        print("6. Check Services")
        print("   - Verify all required services are running")
        print()
        print("0. Exit")
        print("=" * 50)


async def main():
    """Main demo function"""
    print("🎉 Welcome to XAgent E2E Demo!")
    print("This demo showcases the XAgent integration with L3AGI")
    
    demo = E2EDemo()
    
    while True:
        demo.show_demo_menu()
        
        try:
            choice = input("\nSelect a demo task (0-6): ").strip()
            
            if choice == "0":
                print("👋 Goodbye!")
                break
            
            elif choice == "1":
                task = "Search for the latest AI news and provide a comprehensive summary of the top 3 stories"
                result = await demo.run_demo_task(task)
                print(f"\n📰 Task Result:\n{result}")
                
            elif choice == "2":
                task = "Write a Python function to calculate the factorial of a number, including error handling and documentation"
                result = await demo.run_demo_task(task)
                print(f"\n🐍 Task Result:\n{result}")
                
            elif choice == "3":
                task = "Create a text file named 'demo_output.txt' with the content 'Hello from XAgent! This is a demonstration of file editing capabilities.'"
                result = await demo.run_demo_task(task)
                print(f"\n📁 Task Result:\n{result}")
                
            elif choice == "4":
                task = "Explain how machine learning works in simple terms, covering supervised learning, unsupervised learning, and neural networks"
                result = await demo.run_streaming_demo(task)
                print(f"\n🧠 Streaming Task Result:\n{result}")
                
            elif choice == "5":
                custom_task = input("Enter your custom task: ").strip()
                if custom_task:
                    result = await demo.run_demo_task(custom_task)
                    print(f"\n🎯 Custom Task Result:\n{result}")
                else:
                    print("❌ No task entered")
                    
            elif choice == "6":
                if demo.check_services():
                    print("✅ All services are healthy and ready for demo!")
                else:
                    print("❌ Some services are not accessible")
                    print("💡 Start services with: docker-compose -f docker-compose.xagent.yml up -d")
                    
            else:
                print("❌ Invalid choice. Please select 0-6.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Demo interrupted. Goodbye!")
            break
        except Exception as e:
            logger.error(f"Demo error: {e}")
            print(f"❌ Demo error: {e}")
        
        input("\nPress Enter to continue...")


if __name__ == "__main__":
    # Check if we're in the right directory
    if not Path("docker-compose.xagent.yml").exists():
        print("❌ Error: docker-compose.xagent.yml not found")
        print("💡 Please run this script from the team-of-ai-agents directory")
        sys.exit(1)
    
    # Check Python version
    if sys.version_info < (3, 10):
        print("❌ Error: Python 3.10+ is required")
        print(f"💡 Current version: {sys.version}")
        sys.exit(1)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Demo interrupted. Goodbye!")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"💥 Fatal error: {e}")
        sys.exit(1)
