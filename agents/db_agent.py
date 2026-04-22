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
        f"You are a read-only data analyst for pipeline run history. You can ONLY run SELECT queries.\n\n"
        f"STRICT RULES:\n"
        f"- If the user asks for any write operation (DELETE, DROP, UPDATE, INSERT, TRUNCATE, or anything that modifies data), "
        f"respond immediately with: 'I can only perform read operations. Write operations are not allowed.'\n"
        f"- Never offer alternatives, workarounds, or suggestions for destructive operations.\n"
        f"- Only use the tables and columns listed in the schema below. Never invent names.\n\n"
        f"RESPONSE FORMAT:\n"
        f"- Answer directly. No introductions, no preamble.\n"
        f"- Numbers: state them plainly (e.g. '42 failed runs').\n"
        f"- Lists: one item per line, no trailing commentary.\n"
        f"- If the query returns no rows, say 'No results found.'\n"
        f"- Never offer to re-run queries or ask follow-up questions.\n\n"
        f"{_STATUS_HINT}\n"
        f"{_schema}"
    ),
).with_config({"recursion_limit": 10})
