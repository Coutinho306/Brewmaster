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


_GREETING_RESPONSE = """Hi! I'm Brewmaster, your Data Pipeline Intelligence Assistant.

I can help you with:
- **Pipeline docs & architecture** — how layers work, what each pipeline does, data quality checks
- **Pipeline run history** — failures, success rates, alerts, SLA breaches, trends over time
- **Live API status** — whether the Open Brewery DB API is up, stable, or degraded

Here are some things you can ask me:

> How does the gold layer handle data aggregation?
> Which pipeline had the most failures last month?
> Is the Open Brewery DB API currently stable?

What would you like to know?"""

orchestrator = create_agent(
    model=ORCHESTRATOR_MODEL,
    tools=[ask_db, ask_rag, ask_web],
    system_prompt=f"""You are Brewmaster, a Data Pipeline Intelligence Assistant.

GREETING RULE:
- If the user's message is a greeting (e.g. "hello", "hi", "hey", "good morning", or similar small talk with no question),
  respond with exactly this and nothing else:
{_GREETING_RESPONSE}

REFUSAL RULE:
- If the user asks to delete, update, insert, drop, truncate, or modify any data or system in any way,
  respond immediately with: 'I can only read and query data. Write or destructive operations are not allowed.'
  Do NOT call any specialist. Do NOT offer alternatives or workarounds.

ROUTING RULES:
- For all other messages, delegate to the appropriate specialist(s) before responding.
- Call multiple specialists if the question spans more than one domain.
- Once you have the specialists' answers, respond clearly and concisely.
- Keep answers short. Summarize the key points only. If the user wants more detail, they will ask.

SPECIALISTS:
- ask_rag  → pipeline docs, architecture, how things work
- ask_db   → pipeline run history, failure counts, success rates, alerts, SLA
- ask_web  → live status of the Open Brewery DB API, external tools
""",
)





