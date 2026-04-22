#!/bin/bash
set -e

unset VIRTUAL_ENV

echo "=== Brewmaster Setup ==="

# ── 0. OS check ────────────────────────────────────────────────────────────────
OS="$(uname -s 2>/dev/null || echo "Windows")"
if [[ "$OS" == "Darwin" ]]; then
  echo ""
  echo "  ⚠  macOS detected."
  echo "  This script was developed for Linux and may not run correctly."
  echo "  Please follow the macOS setup tutorial in README.md instead."
  echo ""
  exit 1
fi
if [[ "$OS" == "Windows"* ]] || [[ "$OS" == "MINGW"* ]] || [[ "$OS" == "MSYS"* ]] || [[ "$OS" == "CYGWIN"* ]]; then
  echo ""
  echo "  ⚠  Windows detected."
  echo "  This script was developed for Linux and may not run correctly."
  echo "  Please follow the Windows setup tutorial in README.md instead."
  echo ""
  exit 1
fi

# ── 1. Check .env ──────────────────────────────────────────────────────────────
if [ ! -f ".env" ]; then
  cp .env.example .env
  echo ""
  echo "  .env created from .env.example"
  echo "  Fill in your API keys, then re-run: ./setup.sh"
  echo ""
  echo "    OPENAI_API_KEY=sk-...     (required)"
  echo "    TAVILY_API_KEY=tvly-...   (required)"
  echo "    LANGSMITH_API_KEY=...     (optional)"
  echo ""
  exit 0
fi

# ── 2. Validate required API keys ─────────────────────────────────────────────
check_key() {
  local key_name="$1"
  local key_value
  # Strip quotes and spaces from the value
  key_value=$(grep "^${key_name}" .env | sed "s/.*=\s*//" | tr -d "'\""  | tr -d '[:space:]')

  if [ -z "$key_value" ] || [ "$key_value" = "****" ] || [ "$key_value" = "..." ]; then
    echo "  ✗ $key_name is not set"
    return 1
  fi
  echo "  ✓ $key_name"
  return 0
}

echo ""
echo "Checking API keys..."
MISSING=0
check_key "OPENAI_API_KEY"  || MISSING=1
check_key "TAVILY_API_KEY"  || MISSING=1
echo ""

if [ "$MISSING" -eq 1 ]; then
  echo "  Fill in the missing keys in .env, then re-run: ./setup.sh"
  echo ""
  exit 1
fi

# ── 3. Install Python dependencies ────────────────────────────────────────────
echo "[1/3] Installing Python dependencies..."
uv sync --quiet

# ── 4. Seed database (skip if already exists) ─────────────────────────────────
if [ ! -f "data/database/brewmaster.db" ]; then
  echo "[2/3] Seeding database..."
  uv run python data/seed_database.py
else
  echo "[2/3] Database already exists — skipping"
fi

# ── 5. Install UI dependencies + clear stale build cache ──────────────────────
echo "[3/3] Installing UI dependencies..."
cd agent-chat-ui
if [ ! -d "node_modules" ]; then
  pnpm install --silent
else
  echo "      node_modules already present — skipping"
fi
cd ..

# ── 6. Start servers ──────────────────────────────────────────────────────────
echo ""
echo "Starting servers..."
echo ""

# LangGraph server
nohup uv run langgraph dev --no-browser > langgraph.log 2>&1 &
LANGGRAPH_PID=$!
disown $LANGGRAPH_PID
echo "  LangGraph server started (PID $LANGGRAPH_PID) → http://localhost:2024"
echo "  Logs: tail -f langgraph.log"

# Wait for LangGraph to be ready before starting UI
sleep 5

# Agent Chat UI
cd agent-chat-ui
nohup pnpm dev > ../ui.log 2>&1 &
UI_PID=$!
disown $UI_PID
cd ..
echo "  UI started          (PID $UI_PID)          → http://localhost:3000"
echo "  Logs: tail -f ui.log"

echo ""
echo "=== Brewmaster is running ==="
echo ""
echo "  Chat UI   →  http://localhost:3000"
echo ""
echo "  Stop all: kill $LANGGRAPH_PID $UI_PID"
echo ""

# Save PIDs for the stop script
echo "$LANGGRAPH_PID $UI_PID" > .brewmaster.pids
