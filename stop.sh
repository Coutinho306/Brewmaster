#!/bin/bash

# Kill by saved PIDs
if [ -f ".brewmaster.pids" ]; then
  PIDS=$(cat .brewmaster.pids)
  kill $PIDS 2>/dev/null
  rm -f .brewmaster.pids
fi

# Kill anything still holding the ports (catches orphaned child processes)
for PORT in 2024 3000; do
  PIDS_ON_PORT=$(lsof -ti tcp:$PORT 2>/dev/null)
  if [ -n "$PIDS_ON_PORT" ]; then
    kill -9 $PIDS_ON_PORT 2>/dev/null
    echo "  Freed port $PORT"
  fi
done

# Kill any orphaned next/langgraph processes by name
pkill -9 -f "next dev" 2>/dev/null || true
pkill -9 -f "next-server" 2>/dev/null || true
pkill -9 -f "langgraph dev" 2>/dev/null || true

echo "Brewmaster stopped."
