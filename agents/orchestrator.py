from core.config import ORCHESTRATOR_MODEL
from langchain.agents import create_agent
from langchain.tools import tool
from langchain.messages import HumanMessage
from agents import rag_agent, web_agent, db_agent


@tool
def ask_rag(query: str) -> str:
    """RAG Agent searches information about the functionality of the pipeline"""
    try:
        response = rag_agent.invoke({"messages": [HumanMessage(content=query)]})
        return response["messages"][-1].content
    except Exception as e:
        return f"RAG agent error: {e}"


@tool
def ask_web(query: str) -> str:
    """Web Agent searches the web for information about Open Brewery DB API"""
    try:
        response = web_agent.invoke({"messages": [HumanMessage(content=query)]})
        return response["messages"][-1].content
    except Exception as e:
        return f"Web agent error: {e}"


@tool
def ask_db(query: str) -> str:
    """DB Agent queries the database for data information about the pipelines"""
    try:
        response = db_agent.invoke({"messages": [HumanMessage(content=query)]})
        return response["messages"][-1].content
    except Exception as e:
        return f"DB agent error: {e}"


orchestrator = create_agent(
    model=ORCHESTRATOR_MODEL,
    tools=[ask_db, ask_rag, ask_web],
    system_prompt="""
    You are a Pipeline Administrator.
    You should always ask the specialists.
    You can delegate the tasks to your specialists in functionality, API and data information about the pipelines.
    You can call multiple specialists if the user questions needs.
    Once you have received their answers, respond the user.
    """,
)





