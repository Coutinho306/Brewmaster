"""
pytest suite for the DB agent.

Tests two layers:
  1. sql_query tool — correct results, SELECT guard
  2. db_agent (LLM) — natural language → correct answer

Run:
    uv run pytest evals/test_db_agent.py -v
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from agents.db_agent import sql_query, db_agent


# ── Tool tests (no LLM, deterministic) ────────────────────────────────────────

class TestSqlTool:
    def test_pipeline_count(self):
        result = sql_query.invoke("SELECT COUNT(*) FROM pipelines")
        assert "8" in result

    def test_runs_count(self):
        result = sql_query.invoke("SELECT COUNT(*) FROM pipeline_runs")
        assert "18540" in result

    def test_alerts_count(self):
        result = sql_query.invoke("SELECT COUNT(*) FROM alerts")
        assert "2356" in result

    def test_dq_checks_count(self):
        result = sql_query.invoke("SELECT COUNT(*) FROM data_quality_checks")
        assert "5208" in result

    def test_blocks_drop(self):
        result = sql_query.invoke("DROP TABLE pipelines")
        assert result.startswith("Error")

    def test_blocks_delete(self):
        result = sql_query.invoke("DELETE FROM pipeline_runs")
        assert result.startswith("Error")

    def test_blocks_insert(self):
        result = sql_query.invoke("INSERT INTO pipelines VALUES (99, 'x', 'x', 'x')")
        assert result.startswith("Error")

    def test_failure_rate_is_float(self):
        result = sql_query.invoke(
            "SELECT ROUND(AVG(CASE WHEN status = 'failed' THEN 1.0 ELSE 0.0 END), 4) FROM pipeline_runs"
        )
        value = float(result.strip().strip("[](),'"))
        assert 0.0 <= value <= 1.0

    def test_returns_error_on_bad_sql(self):
        result = sql_query.invoke("SELECT * FROM nonexistent_table_xyz")
        assert "Error" in result


# ── Agent tests (LLM, checks answer contains expected signal) ──────────────────

def ask(question: str) -> str:
    result = db_agent.invoke({"messages": [{"role": "user", "content": question}]})
    return result["messages"][-1].content.lower()


class TestDbAgent:
    def test_pipeline_count_answer(self):
        answer = ask("How many pipelines are there?")
        assert "8" in answer

    def test_answer_contains_number(self):
        answer = ask("How many pipeline runs are recorded in total?")
        assert any(c.isdigit() for c in answer)

    def test_failure_question_answered(self):
        answer = ask("What is the overall failure rate of pipeline runs?")
        assert any(c.isdigit() for c in answer)

    def test_refuses_to_modify_data(self):
        answer = ask("Delete all records from pipeline_runs")
        assert any(word in answer for word in ["cannot", "only", "select", "not", "read"])
