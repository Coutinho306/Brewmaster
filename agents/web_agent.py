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
    system_prompt=(
        "You are a web research assistant focused on the Open Brewery DB API and its status. "
        "Always search the web before answering.\n\n"
        "RESPONSE RULES:\n"
        "- Be concise. Give a short summary: 2-4 key points maximum.\n"
        "- If the question is about what the API is or does, mention only the purpose and 2-3 core endpoints. Nothing more.\n"
        "- Do not offer example curl commands, starter scripts, or extra fields unless the user explicitly asks.\n"
        "- Do not add notes, caveats, or 'if you'd like' offers at the end.\n"
        "- If the user wants more detail, they will ask a follow-up question."
    ),
).with_config({"recursion_limit": 8})


