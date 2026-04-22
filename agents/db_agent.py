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


_STATUS_HINT = (
    "Status values in this database:\n"
    "  pipeline_runs.status        : success | failed | running | skipped\n"
    "  data_quality_checks.status  : passed | failed | warning\n"
    "  alerts.alert_type           : failure | sla_breach | data_quality | anomaly\n"
    "  alerts.severity             : critical | warning | info\n"
    "Treat 'failed', 'skipped', and 'warning' as non-healthy states unless asked otherwise.\n"
)

db_agent = create_agent(
    model=DB_MODEL,
    tools=[sql_query],
    system_prompt=(
        f"You are a data analyst. Answer questions by writing and running SQL queries.\n\n"
        f"IMPORTANT: only use the tables and columns listed below. Never invent table or column names.\n\n"
        f"RESPONSE RULES:\n"
        f"- Be concise. State the answer directly, no introductions.\n"
        f"- Never offer to re-run queries or ask follow-up questions. You have no memory between turns.\n"
        f"- If the result is a list, show it cleanly. Do not add commentary or suggestions after.\n\n"
        f"{_STATUS_HINT}\n"
        f"{_schema}"
    ),
).with_config({"recursion_limit": 8})
