"""
Build a SQLite database for the extended dataset (89,740 tracks) and run a
handful of SQL queries that mirror/extend the original analysis — keeping
the SQL layer meaningful on the larger dataset too, not just Python.

Denormalization note: unlike the original star schema (444 artists, 132
genres -> worth normalizing), this dataset's genre dimension is collapsed
to 12 macro-genre buckets used only for aggregation, so it's kept as a
column on the fact table rather than split into a separate dimension table
— normalizing a 12-value low-cardinality column would add a join for no
real benefit. Right-sizing the model to the data is itself the point.

Run: python3 08_build_extended_db.py
"""

import sqlite3
import pandas as pd
from pathlib import Path

df = pd.read_csv("../data_v2/spotify_extended_clean.csv")

conn = sqlite3.connect("../data_v2/spotify_extended.db")
cols = ["track_id", "track_name", "artists", "track_genre", "macro_genre", "popularity",
        "is_hit", "explicit", "danceability", "energy", "loudness", "speechiness",
        "acousticness", "instrumentalness", "liveness", "valence", "tempo",
        "duration_min", "key", "mode", "time_signature"]
df[cols].to_sql("tracks_extended", conn, if_exists="replace", index=False)
conn.execute("CREATE INDEX IF NOT EXISTS idx_ext_genre ON tracks_extended(macro_genre)")
conn.execute("CREATE INDEX IF NOT EXISTS idx_ext_hit ON tracks_extended(is_hit)")
conn.commit()
print(f"tracks_extended: {len(df)} rows -> ../data_v2/spotify_extended.db")

QUERIES = {
"Q1_popularity_by_macro_genre": """
    SELECT macro_genre, COUNT(*) AS n_tracks, ROUND(AVG(popularity),1) AS avg_popularity
    FROM tracks_extended GROUP BY macro_genre ORDER BY avg_popularity DESC
""",
"Q2_hit_rate_by_macro_genre": """
    SELECT macro_genre, COUNT(*) AS n_tracks,
           SUM(is_hit) AS n_hits,
           ROUND(100.0 * SUM(is_hit) / COUNT(*), 2) AS hit_rate_pct
    FROM tracks_extended GROUP BY macro_genre ORDER BY hit_rate_pct DESC
""",
"Q3_explicit_vs_popularity": """
    SELECT explicit, COUNT(*) AS n_tracks, ROUND(AVG(popularity),1) AS avg_popularity
    FROM tracks_extended GROUP BY explicit
""",
"Q4_hits_vs_nonhits_audio_profile": """
    SELECT is_hit,
           COUNT(*) AS n_tracks,
           ROUND(AVG(danceability),3) AS avg_danceability,
           ROUND(AVG(energy),3) AS avg_energy,
           ROUND(AVG(loudness),1) AS avg_loudness,
           ROUND(AVG(instrumentalness),3) AS avg_instrumentalness,
           ROUND(AVG(acousticness),3) AS avg_acousticness
    FROM tracks_extended GROUP BY is_hit
""",
"Q5_volume_vs_hitrate_mismatch": """
    WITH stats AS (
        SELECT macro_genre, COUNT(*) AS n_tracks,
               ROUND(100.0 * SUM(is_hit) / COUNT(*), 2) AS hit_rate_pct,
               RANK() OVER (ORDER BY COUNT(*) DESC) AS volume_rank,
               RANK() OVER (ORDER BY 100.0 * SUM(is_hit) / COUNT(*) DESC) AS hitrate_rank
        FROM tracks_extended GROUP BY macro_genre
    )
    SELECT macro_genre, n_tracks, volume_rank, hit_rate_pct, hitrate_rank,
           (volume_rank - hitrate_rank) AS rank_gap
    FROM stats ORDER BY rank_gap DESC
""",
}

out_dir = Path("../data_v2/query_results")
out_dir.mkdir(exist_ok=True)
for name, sql in QUERIES.items():
    result = pd.read_sql_query(sql, conn)
    result.to_csv(out_dir / f"{name}.csv", index=False)
    print(f"\n=== {name} ===")
    print(result.to_string(index=False))

conn.close()
