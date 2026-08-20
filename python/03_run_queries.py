"""
Execute every query in sql/analysis_queries.sql against spotify.db and save
each result set as a CSV (for the report/dashboard) + print a preview
(as a validation check that every query actually runs and returns sane data).

Run: python3 03_run_queries.py
"""

import sqlite3
import re
import pandas as pd
from pathlib import Path

DB_PATH = "../data/spotify.db"
SQL_PATH = "../sql/analysis_queries.sql"
OUT_DIR = Path("../data/query_results")
OUT_DIR.mkdir(exist_ok=True)

sql_text = Path(SQL_PATH).read_text()

# Split into individual queries using the "-- Qn." comment markers
chunks = re.split(r"-- -+\n-- (Q\d+)\.", sql_text)
# chunks[0] is preamble; then alternating (label, body)
queries = []
for i in range(1, len(chunks), 2):
    label = chunks[i]
    body = chunks[i + 1]
    # strip trailing comment lines, keep the SQL statement itself
    sql_stmt = body.strip()
    queries.append((label, sql_stmt))

conn = sqlite3.connect(DB_PATH)

for label, stmt in queries:
    # First line is the tail of the "-- Qn. <title>" comment (the "-- Qn."
    # part was already consumed by the split regex) — drop it, then strip
    # every remaining comment line. What's left is pure SQL.
    body_lines = stmt.split("\n")[1:]
    sql_lines = [l for l in body_lines if not l.strip().startswith("--")]
    clean_sql = "\n".join(sql_lines).strip().rstrip(";")

    df = pd.read_sql_query(clean_sql, conn)
    out_path = OUT_DIR / f"{label}.csv"
    df.to_csv(out_path, index=False)
    print(f"\n=== {label} === ({len(df)} rows) -> {out_path.name}")
    print(df.head(5).to_string(index=False))

conn.close()
print(f"\nAll {len(queries)} queries executed successfully.")
