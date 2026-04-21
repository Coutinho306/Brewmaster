from core.config import ORCHESTRATOR_MODEL
from langchain.agents import create_agent
from langchain.tools import tool
from langchain.messages import HumanMessage
from agents import rag_agent, web_agent, db_agent


@tool
def ask_rag(query: str) -> str:
    """Rag Agent searches information about the funcionality of the pipeline"""
    response = rag_agent.invoke({"messages": [HumanMessage(content=query)]})
    return response["messages"][-1].content


@tool
def ask_web(query: str) -> str:
    """Web Agent searches the web for information about Open Brewery DB API"""
    response = web_agent.invoke({"messages": [HumanMessage(content=query)]})
    return response["messages"][-1].content


@tool
def ask_db(query: str) -> str:
    """DB Agent queries the database for data information about the pipelines"""
    response = db_agent.invoke({"messages": [HumanMessage(content=query)]})
    return response["messages"][-1].content


orchestrator = create_agent(
    model=ORCHESTRATOR_MODEL,
    tools=[ask_db, ask_rag, ask_web],
    system_prompt="""
    You are a Pipeline Administrator. 
    You should always ask the specialists.
    You can delegate the tasks to your specialists in funcionality, API and data information about the pipelines.
    You can call multiple specialists if the user questions needs.
    Once you have received their answers, respond the user.
    """,
)





