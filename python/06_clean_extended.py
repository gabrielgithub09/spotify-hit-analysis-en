"""
Clean the extended Spotify dataset (114,000 tracks, full popularity range,
114 genres, ~1000 tracks/genre) used to test whether a larger, less biased
dataset changes the conclusions of the original Top-100-only analysis.

Source: "Spotify Tracks Dataset" (maharshipandya), mirrored on GitHub.
Unlike the 2010-2019 Top 100 dataset, this one is NOT restricted to hits:
popularity ranges from 0 to 100 (mean ~33), so it lets us test whether the
original analysis's weak audio-feature/popularity correlations were an
artifact of only ever looking at already-popular songs (range restriction).

Run: python3 06_clean_extended.py
"""

import pandas as pd

RAW_PATH = "../data_v2/spotify_extended_raw.csv"
OUT_PATH = "../data_v2/spotify_extended_clean.csv"

df = pd.read_csv(RAW_PATH)

before = len(df)
df = df.dropna(subset=["track_name", "artists", "popularity"])
print(f"Dropped {before - len(df)} rows with missing key fields")

# The source assigns each track to ONE genre bucket per row, so the same
# track_id can legitimately appear multiple times (once per genre it was
# sampled under). For a track-level popularity/audio-feature analysis we
# want one row per track; we keep the genre of the first occurrence and
# drop the rest, but keep a separate long-form genre table for genre-level
# stats so we don't lose that information entirely.
genre_table = df[["track_id", "track_genre"]].drop_duplicates()
n_dupes = df["track_id"].duplicated().sum()
print(f"{n_dupes} duplicate track_id rows (same track tagged under multiple genres) -> deduped for track-level analysis")
df_unique = df.drop_duplicates(subset="track_id", keep="first").reset_index(drop=True)

# Macro-genre grouping (12 buckets) for readable genre-level charts —
# the raw dataset's 114 micro-genres (e.g. "chicago-house", "detroit-techno",
# "minimal-techno") are too granular to plot directly.
MACRO_GENRE_MAP = {
    "pop": ["pop", "power-pop", "indie-pop", "synth-pop", "j-pop", "k-pop", "mandopop", "cantopop", "pop-film"],
    "rock": ["rock", "alt-rock", "hard-rock", "psych-rock", "punk-rock", "rock-n-roll", "grunge", "j-rock", "rockabilly", "alternative"],
    "hip-hop / r&b": ["hip-hop", "r-n-b"],
    "electronic / dance": ["edm", "electro", "electronic", "house", "deep-house", "chicago-house", "progressive-house",
                            "techno", "detroit-techno", "minimal-techno", "trance", "dubstep", "drum-and-bass",
                            "breakbeat", "idm", "dance", "club", "hardstyle", "trip-hop", "garage", "j-dance"],
    "metal / punk": ["metal", "heavy-metal", "death-metal", "black-metal", "metalcore", "grindcore", "hardcore", "punk", "goth", "industrial"],
    "latin": ["latin", "latino", "reggaeton", "salsa", "samba", "sertanejo", "mpb", "forro", "pagode", "brazil", "tango", "spanish"],
    "jazz / soul / funk": ["jazz", "soul", "funk", "groove", "blues"],
    "folk / country / acoustic": ["folk", "country", "bluegrass", "singer-songwriter", "songwriter", "acoustic", "guitar", "honky-tonk"],
    "classical / instrumental": ["classical", "opera", "piano", "new-age", "ambient", "sleep", "study"],
    "world": ["afrobeat", "indian", "iranian", "malay", "turkish", "swedish", "german", "french", "british", "world-music"],
    "reggae / dub": ["reggae", "reggaeton", "dub", "dancehall", "ska"],
    "other / mood / misc": ["anime", "children", "kids", "comedy", "disney", "gospel", "happy", "sad", "romance",
                             "party", "chill", "show-tunes", "emo"],
}
genre_to_macro = {g: macro for macro, genres in MACRO_GENRE_MAP.items() for g in genres}
df_unique["macro_genre"] = df_unique["track_genre"].map(genre_to_macro).fillna("other / mood / misc")

# Basic typing / hygiene
df_unique["explicit"] = df_unique["explicit"].astype(bool)
df_unique["duration_min"] = (df_unique["duration_ms"] / 60000).round(2)

# A "hit" flag for the hit-vs-non-hit comparison in 07_range_restriction_test.py.
# Threshold chosen to roughly match the average popularity of the original
# Top-100 (2010-2019) dataset (74.8) — i.e. "as popular as an average charting hit".
df_unique["is_hit"] = df_unique["popularity"] >= 70

df_unique.to_csv(OUT_PATH, index=False)
genre_table.to_csv("../data_v2/track_genre_long.csv", index=False)

print(f"\nSaved {len(df_unique)} unique tracks x {len(df_unique.columns)} columns -> {OUT_PATH}")
print(f"Popularity range: {df_unique['popularity'].min()}-{df_unique['popularity'].max()}, mean {df_unique['popularity'].mean():.1f}")
print(f"Hits (popularity >= 70): {df_unique['is_hit'].sum()} ({100*df_unique['is_hit'].mean():.1f}%)")
print(f"Explicit tracks: {df_unique['explicit'].sum()} ({100*df_unique['explicit'].mean():.1f}%)")
