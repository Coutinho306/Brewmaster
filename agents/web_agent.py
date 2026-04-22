from core.config import WEB_MODEL
from tavily import TavilyClient
from typing import Dict, Any
from langchain.agents import create_agent
from langchain.tools import tool

tavily_client = TavilyClient()

@tool
def web_search(query: str) -> Dict[str, Any]:
    """Search the web for information"""
    try:
        return tavily_client.search(query)
    except Exception as e:
        return {"error": str(e), "results": []}

web_agent = create_agent(
    model=WEB_MODEL,
    tools=[web_search],
    system_prompt="You are a helpful assistant that answers questions about the openbrewerydb API. Always search the web before answering.",
).with_config({"recursion_limit": 4})


