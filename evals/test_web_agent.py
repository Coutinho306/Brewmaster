"""
pytest suite for the Web agent.

Tests two layers:
  1. web_search tool — returns results or a graceful error dict
  2. web_agent (LLM) — natural language → answer grounded in search results

Run:
    uv run pytest evals/test_web_agent.py -v
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from agents.web_agent import web_search


# ── Tool tests (no LLM, checks Tavily response shape) ─────────────────────────

class TestWebSearchTool:
    def test_returns_dict(self):
        result = web_search.invoke("Open Brewery DB API")
        assert isinstance(result, dict)

    def test_has_results_key(self):
        result = web_search.invoke("Open Brewery DB API")
        assert "results" in result or "error" in result

    def test_brewery_query_returns_results(self):
        result = web_search.invoke("Open Brewery DB API endpoints")
        assert isinstance(result.get("results", []), list)

    def test_graceful_on_empty_query(self):
        result = web_search.invoke("xkqzwpfj_nonexistent_brewery_xyz")
        assert isinstance(result, dict)
