from core.config import WEB_MODEL
from tavily import TavilyClient
from typing import Dict, Any
from langchain.agents import create_agent
from langchain.tools import tool

tavily_client = TavilyClient()

@tool
def web_search(query: str) -> Dict[str, Any]:
    """Search the web for information"""
    return tavily_client.search(query)

web_agent = create_agent(
    model=WEB_MODEL,
    tools=[web_search],
)


