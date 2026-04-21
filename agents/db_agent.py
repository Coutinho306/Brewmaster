from core.config import DB_MODEL, DB_PATH
from langchain_community.utilities import SQLDatabase
from langchain.tools import tool
from langchain.agents import create_agent


db = SQLDatabase.from_uri(f"sqlite:///{DB_PATH}")
_schema = db.get_table_info()

@tool
def sql_query(query: str) -> str:
    """Executes a read-only SQL SELECT query against the pipeline runs database."""
    if not query.strip().upper().startswith("SELECT"):
        return "Error: only SELECT queries are allowed."
    try:
        return db.run(query)
    except Exception as e:
        return f"Error: {e}"


db_agent = create_agent(
    model=DB_MODEL,
    tools=[sql_query],
    system_prompt=(
        f"You are a data analyst. Answer questions by writing and running SQL queries.\n\n"
        f"IMPORTANT: only use the tables and columns listed below. Never invent table or column names.\n\n"
        f"{_schema}"
    ),
)
