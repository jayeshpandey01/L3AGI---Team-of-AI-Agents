"""
Tool adapter that bridges L3AGI's existing tools with XAgent's ToolServer.
This enables seamless tool execution during the migration.
"""

from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class L3AGIToolAdapter:
    """Bridges L3AGI's existing tools with XAgent's ToolServer"""
    
    def __init__(self):
        self.tool_mapping = self._create_complete_tool_mapping()
        self.rapidapi_tools = self._get_rapidapi_tools()
        self.direct_mapping_tools = self._get_direct_mapping_tools()
        self.python_execution_tools = self._get_python_execution_tools()
    
    def _create_complete_tool_mapping(self) -> Dict[str, str]:
        """Complete mapping of all L3AGI tools to XAgent tools"""
        return {
            # Search tools
            "SerpGoogleSearch": "web_search",
            "DuckDuckGo": "web_search",
            "Bing": "web_search",
            "Wikipedia": "web_search",
            "Arxiv": "web_search",
            
            # Communication tools
            "Twilio": "rapidapi_twilio",
            "SendGrid": "rapidapi_sendgrid",
            "Slack": "rapidapi_slack",
            "Twitter": "rapidapi_twitter",
            "Instagram": "rapidapi_instagram",
            "Gmail": "rapidapi_gmail",
            
            # Data tools
            "PostgresDatabaseTool": "database_postgres",
            "MySQLDatabaseTool": "database_mysql",
            "FileTool": "file_editor",
            
            # AI/ML tools
            "Dalle": "rapidapi_dalle",
            "Chart": "python_notebook",
            "WebScraper": "web_browser",
            
            # Productivity tools
            "GoogleCalendar": "rapidapi_google_calendar",
            "Zapier": "rapidapi_zapier",
            "Cal": "rapidapi_cal",
            
            # Utility tools
            "OpenWeatherMap": "rapidapi_openweather",
            "YouTube": "rapidapi_youtube"
        }
    
    def _get_rapidapi_tools(self) -> List[str]:
        """Tools that use RapidAPI integration"""
        return [
            "Twilio", "SendGrid", "Slack", "Twitter", "Instagram", "Gmail",
            "Dalle", "GoogleCalendar", "Zapier", "Cal", "OpenWeatherMap", "YouTube"
        ]
    
    def _get_direct_mapping_tools(self) -> List[str]:
        """Tools that have direct XAgent equivalents"""
        return [
            "SerpGoogleSearch", "DuckDuckGo", "Bing", "Wikipedia", "Arxiv",
            "PostgresDatabaseTool", "MySQLDatabaseTool", "FileTool", "WebScraper"
        ]
    
    def _get_python_execution_tools(self) -> List[str]:
        """Tools that need Python notebook execution"""
        return ["Chart"]
    
    def adapt_tool_call(self, tool_name: str, tool_args: Dict) -> Dict:
        """Main method to adapt L3AGI tool calls to XAgent format"""
        
        if tool_name in self.rapidapi_tools:
            return self._adapt_rapidapi_tool(tool_name, tool_args)
        elif tool_name in self.direct_mapping_tools:
            return self._adapt_direct_mapping_tool(tool_name, tool_args)
        elif tool_name in self.python_execution_tools:
            return self._adapt_python_execution_tool(tool_name, tool_args)
        else:
            # Fallback to Python notebook for unknown tools
            return self._adapt_unknown_tool(tool_name, tool_args)
    
    def _adapt_rapidapi_tool(self, tool_name: str, tool_args: Dict) -> Dict:
        """Adapt RapidAPI-based tools"""
        rapidapi_mapping = {
            "Twilio": "rapidapi_twilio",
            "SendGrid": "rapidapi_sendgrid",
            "Slack": "rapidapi_slack",
            "Twitter": "rapidapi_twitter",
            "Instagram": "rapidapi_instagram",
            "Gmail": "rapidapi_gmail",
            "Dalle": "rapidapi_dalle",
            "GoogleCalendar": "rapidapi_google_calendar",
            "Zapier": "rapidapi_zapier",
            "Cal": "rapidapi_cal",
            "OpenWeatherMap": "rapidapi_openweather",
            "YouTube": "rapidapi_youtube"
        }
        
        return {
            "tool": rapidapi_mapping.get(tool_name),
            "args": {
                "api_key": tool_args.get("api_key"),
                "action": tool_args.get("action", "execute"),
                "data": {k: v for k, v in tool_args.items() if k not in ["api_key", "action"]}
            }
        }
    
    def _adapt_direct_mapping_tool(self, tool_name: str, tool_args: Dict) -> Dict:
        """Adapt tools with direct XAgent equivalents"""
        xagent_tool = self.tool_mapping.get(tool_name)
        
        if xagent_tool == "web_search":
            return {
                "tool": "web_search",
                "args": {
                    "query": tool_args.get("query", ""),
                    "engine": self._get_search_engine(tool_name),
                    "max_results": tool_args.get("max_results", 10)
                }
            }
        elif xagent_tool in ["database_postgres", "database_mysql"]:
            return {
                "tool": xagent_tool,
                "args": {
                    "connection_string": tool_args.get("connection_string"),
                    "query": tool_args.get("query"),
                    "operation": tool_args.get("operation", "execute")
                }
            }
        elif xagent_tool == "file_editor":
            return {
                "tool": "file_editor",
                "args": {
                    "file_path": tool_args.get("file_path"),
                    "operation": tool_args.get("operation", "read"),
                    "content": tool_args.get("content", "")
                }
            }
        elif xagent_tool == "web_browser":
            return {
                "tool": "web_browser",
                "args": {
                    "url": tool_args.get("url"),
                    "action": "scrape",
                    "selectors": tool_args.get("selectors", {})
                }
            }
        
        return {"tool": xagent_tool, "args": tool_args}
    
    def _adapt_python_execution_tool(self, tool_name: str, tool_args: Dict) -> Dict:
        """Adapt tools that need Python notebook execution"""
        if tool_name == "Chart":
            python_code = self._generate_chart_code(tool_args)
            return {
                "tool": "python_notebook",
                "args": {
                    "code": python_code,
                    "output_files": ["chart.png"],
                    "dependencies": ["matplotlib", "pandas", "numpy"]
                }
            }
        
        return {"tool": "python_notebook", "args": tool_args}
    
    def _adapt_unknown_tool(self, tool_name: str, tool_args: Dict) -> Dict:
        """Fallback for unknown tools - execute via Python notebook"""
        python_code = f"""
# L3AGI Tool: {tool_name}
# Arguments: {tool_args}

try:
    # Attempt to execute tool logic
    result = execute_{tool_name.lower()}({tool_args})
    print(f"Tool {tool_name} executed successfully: {{result}}")
except Exception as e:
    print(f"Error executing {tool_name}: {{e}}")
"""
        
        return {
            "tool": "python_notebook",
            "args": {
                "code": python_code,
                "dependencies": ["requests", "pandas", "numpy"]
            }
        }
    
    def _get_search_engine(self, tool_name: str) -> str:
        """Get search engine name from tool name"""
        engine_mapping = {
            "SerpGoogleSearch": "google",
            "DuckDuckGo": "duckduckgo",
            "Bing": "bing",
            "Wikipedia": "wikipedia",
            "Arxiv": "arxiv"
        }
        return engine_mapping.get(tool_name, "google")
    
    def _generate_chart_code(self, tool_args: Dict) -> str:
        """Generate Python code for chart creation"""
        return f"""
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# Chart configuration
chart_type = "{tool_args.get('chart_type', 'line')}"
data = {tool_args.get('data', '[]')}
title = "{tool_args.get('title', 'Chart')}"
x_label = "{tool_args.get('x_label', 'X')}"
y_label = "{tool_args.get('y_label', 'Y')}"

# Create chart
fig, ax = plt.subplots(figsize=(10, 6))

if chart_type == 'line':
    ax.plot(data)
elif chart_type == 'bar':
    ax.bar(range(len(data)), data)
elif chart_type == 'scatter':
    x_data = [d[0] for d in data]
    y_data = [d[1] for d in data]
    ax.scatter(x_data, y_data)

ax.set_title(title)
ax.set_xlabel(x_label)
ax.set_ylabel(y_label)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('chart.png', dpi=300, bbox_inches='tight')
print("Chart generated successfully as chart.png")
"""
    
    def get_available_tools(self) -> List[str]:
        """Get list of available XAgent tools"""
        return list(set(self.tool_mapping.values()))
    
    def is_tool_supported(self, tool_name: str) -> bool:
        """Check if a tool is supported by XAgent"""
        return tool_name in self.tool_mapping
    
    def get_tool_mapping_info(self) -> Dict[str, str]:
        """Get detailed tool mapping information"""
        return self.tool_mapping.copy()
