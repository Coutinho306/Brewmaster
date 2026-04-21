from pathlib import Path
from dotenv import load_dotenv

# Works regardless of where the script is called from
ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

CHROMA_PATH    = str(ROOT / "data" / "chroma")
DB_PATH        = str(ROOT / "data" / "database" / "brewmaster.db")
COLLECTION     = "bees_docs"

RAG_MODEL      = "gpt-5-nano"
DB_MODEL       = "gpt-5-nano"
WEB_MODEL      = "gpt-5-nano"
ORCHESTRATOR_MODEL = "gpt-5-nano"
