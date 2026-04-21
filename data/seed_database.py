"""
Brewmaster — seed script.
Generates a SQLite DB with fictional pipeline run history inspired by the
Bees-Brewery-Pipeline medallion architecture (Bronze → Silver → Gold).

Run:  uv run python data/seed_database.py
"""

import sqlite3
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path
from faker import Faker

fake = Faker()
random.seed(42)

DB_PATH = Path(__file__).parent / "database" / "brewmaster.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# ── Schema ─────────────────────────────────────────────────────────────────────

SCHEMA = """
CREATE TABLE IF NOT EXISTS pipelines (
    id          INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    description TEXT,
    schedule    TEXT,
    owner       TEXT,
    criticality TEXT CHECK(criticality IN ('high','medium','low')),
    layer       TEXT CHECK(layer IN ('ingestion','bronze','silver','gold','monitoring')),
    source      TEXT,
    destination TEXT
);

CREATE TABLE IF NOT EXISTS pipeline_runs (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    pipeline_id      INTEGER REFERENCES pipelines(id),
    status           TEXT CHECK(status IN ('success','failed','running','skipped')),
    start_time       TEXT,
    end_time         TEXT,
    duration_seconds INTEGER,
    rows_processed   INTEGER,
    error_message    TEXT,
    triggered_by     TEXT CHECK(triggered_by IN ('schedule','manual','upstream'))
);

CREATE TABLE IF NOT EXISTS alerts (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    pipeline_id  INTEGER REFERENCES pipelines(id),
    run_id       INTEGER REFERENCES pipeline_runs(id),
    alert_type   TEXT CHECK(alert_type IN ('failure','sla_breach','data_quality','anomaly')),
    severity     TEXT CHECK(severity IN ('critical','warning','info')),
    message      TEXT,
    created_at   TEXT,
    resolved_at  TEXT,
    resolved_by  TEXT
);

CREATE TABLE IF NOT EXISTS data_quality_checks (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    pipeline_id  INTEGER REFERENCES pipelines(id),
    run_id       INTEGER REFERENCES pipeline_runs(id),
    check_name   TEXT,
    status       TEXT CHECK(status IN ('passed','failed','warning')),
    rows_total   INTEGER,
    rows_failed  INTEGER,
    checked_at   TEXT
);
"""

# ── Static data ────────────────────────────────────────────────────────────────
# Mirrors the real Bees-Brewery-Pipeline DAG structure + typical DE additions

PIPELINES = [
    # (name, description, schedule, owner, criticality, layer, source, destination)
    (
        "bees_bronze_brewery_ingestion",
        "Fetch all breweries from Open Brewery DB API via pagination and store raw JSON",
        "0 6 * * *", "thiago.coutinho", "high", "bronze",
        "Open Brewery DB API", "data/bronze/",
    ),
    (
        "bees_silver_brewery_transform",
        "Cleanse bronze JSON: fill nulls, deduplicate by brewery ID, convert to Parquet partitioned by state/country",
        "@dataset_trigger", "thiago.coutinho", "high", "silver",
        "data/bronze/", "data/silver/",
    ),
    (
        "bees_gold_brewery_aggregations",
        "Build Gold aggregation tables: breweries by type, breweries by state",
        "@dataset_trigger", "thiago.coutinho", "high", "gold",
        "data/silver/", "data/gold/",
    ),
    (
        "bees_data_quality_monitor",
        "Run data quality checks across Bronze/Silver/Gold: min records, required fields, unique IDs",
        "30 6 * * *", "thiago.coutinho", "medium", "monitoring",
        "data/bronze/ + data/silver/ + data/gold/", "Alerts",
    ),
    (
        "brewery_api_health_check",
        "Ping Open Brewery DB API and alert if response time > 5s or non-200 status",
        "*/15 * * * *", "thiago.coutinho", "medium", "monitoring",
        "Open Brewery DB API", "Slack",
    ),
    (
        "silver_schema_drift_detector",
        "Detect schema drift between Bronze and Silver layers, alert on new/removed fields",
        "0 7 * * *", "thiago.coutinho", "medium", "monitoring",
        "data/bronze/ + data/silver/", "Slack",
    ),
    (
        "gold_freshness_sla_check",
        "Verify Gold layer is updated within SLA window. Alert Finance if stale.",
        "0 8 * * *", "thiago.coutinho", "high", "monitoring",
        "data/gold/", "PagerDuty",
    ),
    (
        "brewery_type_trend_report",
        "Weekly aggregation of brewery type distribution trends for the analytics dashboard",
        "0 9 * * 1", "thiago.coutinho", "low", "gold",
        "data/gold/", "Dashboard",
    ),
]

ERROR_MESSAGES = [
    "Open Brewery DB API returned 503 after 3 retries",
    "Connection timeout: API host unreachable after 30s",
    "Data quality check failed: 0 records fetched (min expected: 100)",
    "Schema mismatch: field 'brewery_type' missing in 3 records",
    "Parquet write failed: disk quota exceeded on /data/silver",
    "Deduplication error: duplicate brewery IDs found after join",
    "Gold aggregation failed: silver partition for state='unknown' is empty",
    "API rate limit hit: 429 after 500 requests",
    "JSON decode error on page 47: unexpected EOF",
    "Airflow worker OOM: task killed after exceeding 2GB memory limit",
]

DQ_CHECKS = [
    "min_record_count",
    "required_fields_not_null",
    "unique_brewery_id",
    "valid_brewery_type",
    "state_country_not_null",
    "parquet_row_count_match",
    "gold_aggregation_sum_check",
]


def rand_status(criticality: str) -> str:
    if criticality == "high":
        weights = [87, 9, 2, 2]
    elif criticality == "medium":
        weights = [80, 13, 4, 3]
    else:
        weights = [75, 15, 5, 5]
    return random.choices(["success", "failed", "running", "skipped"], weights=weights)[0]


def seed(conn: sqlite3.Connection):
    cur = conn.cursor()
    cur.executescript(SCHEMA)

    # Pipelines
    for i, p in enumerate(PIPELINES, start=1):
        cur.execute(
            "INSERT INTO pipelines (id,name,description,schedule,owner,criticality,layer,source,destination) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (i, *p),
        )

    now = datetime.now(timezone.utc)

    for pipeline_id, (_, _, schedule, _, criticality, *_rest) in enumerate(PIPELINES, start=1):
        runs_per_day = 96 if "*/15" in schedule else 1

        for day_offset in range(180, 0, -1):
            run_date = now - timedelta(days=day_offset)
            for _ in range(runs_per_day):
                status = rand_status(criticality)
                start = run_date + timedelta(minutes=random.randint(0, 1380))
                duration = random.randint(20, 900) if status != "skipped" else 0
                end = start + timedelta(seconds=duration) if status not in ("running", "skipped") else None
                rows = (
                    random.randint(500, 80_000) if status == "success"
                    else random.randint(0, 500) if status == "failed"
                    else None
                )
                error = random.choice(ERROR_MESSAGES) if status == "failed" else None
                trigger = random.choices(
                    ["schedule", "manual", "upstream"], weights=[75, 10, 15]
                )[0]

                cur.execute(
                    "INSERT INTO pipeline_runs (pipeline_id,status,start_time,end_time,duration_seconds,rows_processed,error_message,triggered_by) "
                    "VALUES (?,?,?,?,?,?,?,?)",
                    (
                        pipeline_id, status,
                        start.isoformat(),
                        end.isoformat() if end else None,
                        duration, rows, error, trigger,
                    ),
                )
                run_id = cur.lastrowid

                if status == "failed":
                    sev = "critical" if criticality == "high" else "warning"
                    created_at = start + timedelta(minutes=random.randint(1, 5))
                    resolved_at = (
                        created_at + timedelta(hours=random.randint(1, 6))
                        if random.random() > 0.3 else None
                    )
                    cur.execute(
                        "INSERT INTO alerts (pipeline_id,run_id,alert_type,severity,message,created_at,resolved_at,resolved_by) "
                        "VALUES (?,?,?,?,?,?,?,?)",
                        (
                            pipeline_id, run_id, "failure", sev, error,
                            created_at.isoformat(),
                            resolved_at.isoformat() if resolved_at else None,
                            fake.name() if resolved_at else None,
                        ),
                    )

                if status == "success" and random.random() < 0.35:
                    check = random.choice(DQ_CHECKS)
                    dq_status = random.choices(
                        ["passed", "failed", "warning"], weights=[85, 5, 10]
                    )[0]
                    rows_total = rows or random.randint(500, 50_000)
                    rows_failed = int(rows_total * random.uniform(0.01, 0.05)) if dq_status != "passed" else 0
                    cur.execute(
                        "INSERT INTO data_quality_checks (pipeline_id,run_id,check_name,status,rows_total,rows_failed,checked_at) "
                        "VALUES (?,?,?,?,?,?,?)",
                        (
                            pipeline_id, run_id, check, dq_status,
                            rows_total, rows_failed,
                            (end or start).isoformat(),
                        ),
                    )

    conn.commit()

    cur.execute("SELECT COUNT(*) FROM pipeline_runs")
    n_runs = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM alerts")
    n_alerts = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM data_quality_checks")
    n_dq = cur.fetchone()[0]

    print(f"✓  {DB_PATH}")
    print(f"   pipelines : {len(PIPELINES)}")
    print(f"   runs      : {n_runs:,}")
    print(f"   alerts    : {n_alerts:,}")
    print(f"   dq checks : {n_dq:,}")


if __name__ == "__main__":
    if DB_PATH.exists():
        DB_PATH.unlink()
    with sqlite3.connect(DB_PATH) as conn:
        seed(conn)
