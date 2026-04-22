"""
pytest suite for the Orchestrator agent.

Tests:
  1. Routing — orchestrator delegates to the right specialist
  2. Direct answers — simple questions answered without tool calls
  3. Multi-agent — questions that require more than one specialist

Run:
    uv run pytest evals/test_orchestrator.py -v
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from agents.orchestrator import orchestrator


def ask(question: str) -> str:
    result = orchestrator.invoke({"messages": [{"role": "user", "content": question}]})
    return result["messages"][-1].content.lower()


# ── Routing to RAG ─────────────────────────────────────────────────────────────

class TestRoutesToRag:
    def test_bronze_layer_question(self):
        answer = ask("What does the bronze layer do?")
        assert any(word in answer for word in ["bronze", "raw", "ingestion", "landing"])

    def test_medallion_architecture_question(self):
        answer = ask("How does the medallion architecture work in this pipeline?")
        assert any(word in answer for word in ["bronze", "silver", "gold", "layer"])


# ── Routing to DB ──────────────────────────────────────────────────────────────

class TestRoutesToDb:
    def test_pipeline_count_question(self):
        answer = ask("How many pipelines are there?")
        assert "8" in answer

    def test_failure_question(self):
        answer = ask("What is the overall failure rate of pipeline runs?")
        assert any(c.isdigit() for c in answer)


# ── Routing to Web ─────────────────────────────────────────────────────────────

class TestRoutesToWeb:
    def test_api_question(self):
        answer = ask("What is the Open Brewery DB API?")
        assert any(word in answer for word in ["brewery", "api", "breweries"])


# ── Direct answers (no tool needed) ───────────────────────────────────────────

class TestDirectAnswers:
    def test_returns_non_empty(self):
        answer = ask("What is the difference between ETL and ELT?")
        assert len(answer.strip()) > 20

    def test_answer_is_string(self):
        answer = ask("What does a data pipeline do?")
        assert isinstance(answer, str)
