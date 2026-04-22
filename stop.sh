#!/bin/bash

# Kill by saved PIDs (force)
if [ -f ".brewmaster.pids" ]; then
  PIDS=$(cat .brewmaster.pids)
  kill -9 $PIDS 2>/dev/null
  rm -f .brewmaster.pids
fi

# Kill any orphaned next/langgraph processes by name
pkill -9 -f "next dev" 2>/dev/null || true
pkill -9 -f "next-server" 2>/dev/null || true
pkill -9 -f "langgraph dev" 2>/dev/null || true

# Free ports — fuser is faster on Linux/WSL, lsof on macOS
for PORT in 2024 3000; do
  if command -v fuser &>/dev/null; then
    fuser -k ${PORT}/tcp 2>/dev/null && echo "  Freed port $PORT" || true
  else
    lsof -ti tcp:${PORT} 2>/dev/null | xargs kill -9 2>/dev/null && echo "  Freed port $PORT" || true
  fi
done

echo "Brewmaster stopped."
