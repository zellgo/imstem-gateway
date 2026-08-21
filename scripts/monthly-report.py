#!/usr/bin/env python3
"""Export monthly spend from LiteLLM Postgres tables."""
from __future__ import annotations

import argparse
import csv
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

try:
    import psycopg
except ImportError:
    sys.stderr.write("Install psycopg:  pip install 'psycopg[binary]'\n")
    sys.exit(1)


def load_env(root: Path) -> None:
    env = root / ".env"
    if not env.exists():
        return
    for line in env.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k, v)


def month_bounds(yyyy_mm: str) -> tuple[str, str]:
    year, month = map(int, yyyy_mm.split("-"))
    start = datetime(year, month, 1, tzinfo=timezone.utc)
    if month == 12:
        end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        end = datetime(year, month + 1, 1, tzinfo=timezone.utc)
    return start.isoformat(), end.isoformat()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--month", default=datetime.now(timezone.utc).strftime("%Y-%m"))
    parser.add_argument("--out", default="")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    load_env(root)
    dsn = os.environ.get("LITELLM_DATABASE_URL") or os.environ.get("DATABASE_URL")
    if not dsn:
        sys.stderr.write("DATABASE_URL / LITELLM_DATABASE_URL is not set\n")
        return 1

    start, end = month_bounds(args.month)
    out = Path(args.out) if args.out else root / "reports" / f"{args.month}-usage.csv"
    out.parent.mkdir(parents=True, exist_ok=True)

    sql = """
    SELECT
      COALESCE(user_id, '') AS employee_id,
      COALESCE(metadata->>'department', '') AS department,
      COALESCE(metadata->>'kind', '') AS key_kind,
      COALESCE(key_alias, api_key, '') AS key_alias,
      COALESCE(model_group, model, '') AS model,
      COALESCE(custom_llm_provider, '') AS provider,
      COUNT(*) AS request_count,
      COALESCE(SUM(prompt_tokens), 0) AS input_tokens,
      COALESCE(SUM(completion_tokens), 0) AS output_tokens,
      COALESCE(SUM(total_tokens), 0) AS total_tokens,
      COALESCE(SUM(spend), 0) AS cost_usd
    FROM "LiteLLM_SpendLogs"
    WHERE "startTime" >= %s AND "startTime" < %s
    GROUP BY 1,2,3,4,5,6
    ORDER BY cost_usd DESC
    """

    rows = []
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            try:
                cur.execute(sql, (start, end))
                cols = [c.name for c in cur.description]
                rows = [dict(zip(cols, r)) for r in cur.fetchall()]
            except psycopg.errors.UndefinedTable:
                conn.rollback()
                sys.stderr.write(
                    "LiteLLM_SpendLogs does not exist yet. Start LiteLLM once so it can migrate the schema.\n"
                )
                return 2

    with out.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "employee_id",
                "department",
                "key_kind",
                "key_alias",
                "model",
                "provider",
                "request_count",
                "input_tokens",
                "output_tokens",
                "total_tokens",
                "cost_usd",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    by_emp = defaultdict(float)
    by_dept = defaultdict(float)
    by_model = defaultdict(float)
    total = 0.0
    for r in rows:
        cost = float(r["cost_usd"] or 0)
        total += cost
        by_emp[r["employee_id"] or "(none)"] += cost
        by_dept[r["department"] or "(none)"] += cost
        by_model[r["model"] or "(none)"] += cost

    print(f"Month {args.month}")
    print(f"Company total spend: ${total:.4f}")
    print("By department:")
    for k, v in sorted(by_dept.items(), key=lambda kv: -kv[1]):
        print(f"  {k:16} ${v:.4f}")
    print("By employee:")
    for k, v in sorted(by_emp.items(), key=lambda kv: -kv[1]):
        print(f"  {k:16} ${v:.4f}")
    print("By model:")
    for k, v in sorted(by_model.items(), key=lambda kv: -kv[1]):
        print(f"  {k:24} ${v:.4f}")
    print(f"CSV: {out}")
    host = urlparse(dsn).hostname
    print(f"Source DB host: {host}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
