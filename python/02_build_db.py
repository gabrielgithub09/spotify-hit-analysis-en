"""
Build a small star-schema SQLite database from the cleaned Spotify CSV.

Why a star schema (fact + dimensions) instead of one flat table?
- It's the same modeling pattern Power BI expects (a fact table linked to
  lookup/dimension tables), so the SQL layer and the future Power BI data
  model line up exactly.
- It lets the SQL queries demonstrate real joins and foreign keys instead of
  querying a single denormalized sheet — more representative of what an
  analyst does on the job, and a better interview talking point.

Tables:
- dim_artist(artist_id, artist_name, artist_type)
- dim_genre(genre_id, genre_name)
- fact_songs(song_id, title, chart_year, chart_position, year_released,
             date_added, tempo_bpm, energy, danceability, loudness_db,
             liveness, valence, duration_sec, duration_min, acousticness,
             speechiness, popularity, popularity_tier, decade_released,
             high_speechiness_flag, is_reappearing_hit,
             artist_id FK, genre_id FK)

Run: python3 02_build_db.py
"""

import sqlite3
import pandas as pd

CSV_PATH = "../data/spotify_clean.csv"
DB_PATH = "../data/spotify.db"

df = pd.read_csv(CSV_PATH)

# --- Dimension: artists -----------------------------------------------------
dim_artist = (
    df[["artist", "artist_type"]]
    .drop_duplicates(subset=["artist"])
    .reset_index(drop=True)
    .rename(columns={"artist": "artist_name"})
)
dim_artist.insert(0, "artist_id", range(1, len(dim_artist) + 1))

# --- Dimension: genres -------------------------------------------------------
dim_genre = (
    df[["genre"]]
    .drop_duplicates()
    .reset_index(drop=True)
    .rename(columns={"genre": "genre_name"})
)
dim_genre.insert(0, "genre_id", range(1, len(dim_genre) + 1))

# --- Fact: songs --------------------------------------------------------------
fact_songs = df.merge(dim_artist, left_on="artist", right_on="artist_name") \
               .merge(dim_genre, left_on="genre", right_on="genre_name")

fact_cols = [
    "title", "chart_year", "chart_position", "year_released", "date_added",
    "tempo_bpm", "energy", "danceability", "loudness_db", "liveness", "valence",
    "duration_sec", "duration_min", "acousticness", "speechiness", "popularity",
    "popularity_tier", "decade_released", "high_speechiness_flag",
    "is_reappearing_hit", "artist_id", "genre_id",
]
fact_songs = fact_songs[fact_cols].reset_index(drop=True)
fact_songs.insert(0, "song_id", range(1, len(fact_songs) + 1))

# --- Write to SQLite -----------------------------------------------------------
conn = sqlite3.connect(DB_PATH)
dim_artist.to_sql("dim_artist", conn, if_exists="replace", index=False)
dim_genre.to_sql("dim_genre", conn, if_exists="replace", index=False)
fact_songs.to_sql("fact_songs", conn, if_exists="replace", index=False)

conn.execute("CREATE INDEX IF NOT EXISTS idx_fact_artist ON fact_songs(artist_id)")
conn.execute("CREATE INDEX IF NOT EXISTS idx_fact_genre ON fact_songs(genre_id)")
conn.execute("CREATE INDEX IF NOT EXISTS idx_fact_year ON fact_songs(chart_year)")
conn.commit()

print(f"dim_artist: {len(dim_artist)} rows")
print(f"dim_genre:  {len(dim_genre)} rows")
print(f"fact_songs: {len(fact_songs)} rows")
print(f"-> {DB_PATH}")
conn.close()
