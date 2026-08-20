"""
Spotify Top 100 Songs 2010-2019 — Data Cleaning & Feature Engineering
======================================================================
Source data: Kaggle "Top Spotify songs from 2010-2019 by year"
(https://www.kaggle.com/datasets/leonardopena/top-spotify-songs-from-20102019-by-year)
enriched by the project team with an "artist type" column.

This script:
1. Loads the raw Excel export (sheet "2010-2019").
2. Renames cryptic/abbreviated columns to explicit, self-documenting names.
3. Fixes data types, strips a stray pivot-table artifact column.
4. Flags duplicate track entries (same song charting in several years).
5. Engineers a few analysis-ready features (decade bucket, popularity tier,
   explicit-content proxy, duration in minutes).
6. Writes a clean CSV that feeds both the SQL database and Power BI.

Run: python3 01_clean_data.py
"""

import pandas as pd

RAW_PATH = "../data/spotify_raw.xlsx"
OUT_PATH = "../data/spotify_clean.csv"

# ---------------------------------------------------------------------------
# 1. Load
# ---------------------------------------------------------------------------
df = pd.read_excel(RAW_PATH, sheet_name="2010-2019")

# ---------------------------------------------------------------------------
# 2. Rename columns — the original export used single-letter / abbreviated
#    headers inherited from the Kaggle source. We make them explicit so the
#    dataset is self-explanatory in SQL, Python and Power BI alike.
# ---------------------------------------------------------------------------
df = df.rename(columns={
    "L": "title",
    "r": "chart_position",      # position within that year's top 100
    "rank": "artist",           # mislabeled in the source export
    "top genre": "genre",
    "year released": "year_released",
    "added": "date_added",
    "bpm": "tempo_bpm",
    "nrgy": "energy",
    "dnce": "danceability",
    "dB": "loudness_db",
    "live": "liveness",
    "val": "valence",
    "dur": "duration_sec",
    "acous": "acousticness",
    "spch": "speechiness",
    "pop": "popularity",
    "top year": "chart_year",   # the top-100-of-the-year this row belongs to
    "artist type": "artist_type",
})

# Drop the stray pivot-table leftover column ("nombre de dance pop", 100% NaN)
df = df.drop(columns=[c for c in df.columns if c == "nombre de dance pop"])

# ---------------------------------------------------------------------------
# 3. Types & basic hygiene
# ---------------------------------------------------------------------------
df["date_added"] = pd.to_datetime(df["date_added"], format="%Y‑%m‑%d", errors="coerce")

# Data-quality issue found during exploration: a handful of song titles are
# purely numeric ("212", "3005", "22", "1950", "17") and Excel silently
# auto-typed those cells as numbers instead of text. One title, Beyoncé's
# "7/11", was even auto-converted to a DATE FRACTION (7/11 -> 0.636363...) —
# a classic Excel autocorrect trap. We force everything back to string
# *before* trimming whitespace so these rows survive instead of becoming NaN.
KNOWN_EXCEL_CORRUPTIONS = {
    ("0.636364", "Beyoncé"): "7/11",
}
df["title"] = df["title"].astype(str).str.strip()
df["artist"] = df["artist"].astype(str).str.strip()
for (bad_title, artist), fixed_title in KNOWN_EXCEL_CORRUPTIONS.items():
    df.loc[(df["title"].str.startswith(bad_title[:6])) & (df["artist"] == artist), "title"] = fixed_title

df["genre"] = df["genre"].astype(str).str.strip().str.lower()
df["artist_type"] = df["artist_type"].astype(str).str.strip()

numeric_cols = ["tempo_bpm", "energy", "danceability", "loudness_db", "liveness",
                 "valence", "duration_sec", "acousticness", "speechiness", "popularity"]
for c in numeric_cols:
    df[c] = pd.to_numeric(df[c], errors="coerce")

before = len(df)
df = df.dropna(subset=["title", "artist", "genre"])
print(f"Dropped {before - len(df)} rows with missing key fields")

# Duplicate check: same title+artist can legitimately reappear in several
# chart_years (a song stays popular across two years). We keep those rows —
# they are real chart appearances — but flag exact full-row duplicates.
exact_dupes = df.duplicated(subset=["title", "artist", "chart_year"]).sum()
print(f"Exact (title, artist, chart_year) duplicates found: {exact_dupes}")
df = df.drop_duplicates(subset=["title", "artist", "chart_year"])

# ---------------------------------------------------------------------------
# 4. Feature engineering
# ---------------------------------------------------------------------------
df["duration_min"] = (df["duration_sec"] / 60).round(2)

df["decade_released"] = (df["year_released"] // 10 * 10).astype(int)

df["popularity_tier"] = pd.cut(
    df["popularity"],
    bins=[-1, 59, 74, 89, 100],
    labels=["Low (<60)", "Mid (60-74)", "High (75-89)", "Very High (90+)"],
)

# Speechiness > 0.33 is the industry rule of thumb for likely spoken-word /
# explicit-leaning content; used later as a proxy since the dataset has no
# native "explicit" flag.
df["high_speechiness_flag"] = df["speechiness"] > 33

df["is_reappearing_hit"] = df.duplicated(subset=["title", "artist"], keep=False)

# ---------------------------------------------------------------------------
# 5. Save
# ---------------------------------------------------------------------------
df = df.sort_values(["chart_year", "chart_position"]).reset_index(drop=True)
df.to_csv(OUT_PATH, index=False)

print(f"\nSaved {len(df)} rows x {len(df.columns)} columns -> {OUT_PATH}")
print(df.dtypes)
