"""
Static charts for the Word report, built with matplotlib using the project's
validated palette (blue/orange/aqua categorical, blue<->red diverging).

Run: python3 05_charts.py
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import pandas as pd
import numpy as np
from pathlib import Path

OUT = Path("../docs/assets")
OUT.mkdir(parents=True, exist_ok=True)

# Palette (see dataviz skill reference palette)
BLUE = "#2a78d6"
ORANGE = "#eb6834"
AQUA = "#1baf7a"
RED = "#e34948"
GRAY_MID = "#f0efec"
INK = "#0b0b0b"
INK_SECONDARY = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"

plt.rcParams.update({
    "font.family": "sans-serif",
    "text.color": INK,
    "axes.edgecolor": GRID,
    "axes.labelcolor": INK_SECONDARY,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "figure.facecolor": "#fcfcfb",
    "axes.facecolor": "#fcfcfb",
})

df = pd.read_csv("../data/spotify_clean.csv")

# ---------------------------------------------------------------------------
# Chart 1 — Top 10 genres by chart appearances (horizontal bar, single hue)
# ---------------------------------------------------------------------------
genre_counts = df["genre"].value_counts().head(10).sort_values()

fig, ax = plt.subplots(figsize=(8, 5))
bars = ax.barh(genre_counts.index, genre_counts.values, color=BLUE, height=0.6)
for b, v in zip(bars, genre_counts.values):
    ax.text(v + 3, b.get_y() + b.get_height() / 2, str(v), va="center", fontsize=9, color=INK_SECONDARY)
ax.set_title("Top 10 genres by chart appearances (2010-2019)", fontsize=13, color=INK, loc="left", pad=12)
ax.set_xlabel("Number of chart appearances")
ax.spines[["top", "right", "left"]].set_visible(False)
ax.grid(axis="x", color=GRID, linewidth=0.8)
ax.set_axisbelow(True)
plt.tight_layout()
plt.savefig(OUT / "chart_top_genres.png", dpi=200)
plt.close()

# ---------------------------------------------------------------------------
# Chart 2 — Average audio features trend by year (3 series line chart)
# ---------------------------------------------------------------------------
yearly = df.groupby("chart_year")[["energy", "danceability", "valence"]].mean()

fig, ax = plt.subplots(figsize=(9, 5))
ax.plot(yearly.index, yearly["energy"], color=BLUE, linewidth=2, marker="o", markersize=5, label="Energy")
ax.plot(yearly.index, yearly["danceability"], color=ORANGE, linewidth=2, marker="o", markersize=5, label="Danceability")
ax.plot(yearly.index, yearly["valence"], color=AQUA, linewidth=2, marker="o", markersize=5, label="Valence (positivity)")
ax.set_title("Average audio features of top-100 songs, 2010-2019", fontsize=13, color=INK, loc="left", pad=12)
ax.set_ylabel("Average score (0-100)")
ax.spines[["top", "right"]].set_visible(False)
ax.grid(axis="y", color=GRID, linewidth=0.8)
ax.set_axisbelow(True)
ax.set_xticks(yearly.index)
ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=3)
plt.tight_layout()
plt.savefig(OUT / "chart_feature_trends.png", dpi=200)
plt.close()

# ---------------------------------------------------------------------------
# Chart 3 — Correlation heatmap (diverging blue<->red, gray midpoint)
# ---------------------------------------------------------------------------
from matplotlib.colors import LinearSegmentedColormap
diverging_cmap = LinearSegmentedColormap.from_list("diverging", [BLUE, GRAY_MID, RED])

FEATURES = ["tempo_bpm", "energy", "danceability", "loudness_db", "liveness",
            "valence", "duration_sec", "acousticness", "speechiness", "popularity"]
corr = df[FEATURES].corr().round(2)

fig, ax = plt.subplots(figsize=(9, 8))
im = ax.imshow(corr.values, cmap=diverging_cmap, vmin=-1, vmax=1)
ax.set_xticks(range(len(FEATURES)))
ax.set_yticks(range(len(FEATURES)))
ax.set_xticklabels(FEATURES, rotation=45, ha="right", fontsize=9)
ax.set_yticklabels(FEATURES, fontsize=9)
for i in range(len(FEATURES)):
    for j in range(len(FEATURES)):
        v = corr.values[i, j]
        color = "white" if abs(v) > 0.6 else INK
        ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=7.5, color=color)
ax.set_title("Correlation matrix — audio features & popularity", fontsize=13, color=INK, loc="left", pad=14)
cbar = fig.colorbar(im, ax=ax, shrink=0.8)
cbar.ax.tick_params(labelsize=8, color=MUTED)
plt.tight_layout()
plt.savefig(OUT / "chart_correlation_heatmap.png", dpi=200)
plt.close()

# ---------------------------------------------------------------------------
# Chart 4 — Popularity by artist configuration (bar)
# ---------------------------------------------------------------------------
by_type = df.groupby("artist_type")["popularity"].mean().sort_values(ascending=False)
fig, ax = plt.subplots(figsize=(7, 4.5))
bars = ax.bar(by_type.index, by_type.values, color=BLUE, width=0.55)
for b, v in zip(bars, by_type.values):
    ax.text(b.get_x() + b.get_width() / 2, v + 0.5, f"{v:.1f}", ha="center", fontsize=9, color=INK_SECONDARY)
ax.set_title("Average popularity by artist configuration", fontsize=13, color=INK, loc="left", pad=12)
ax.set_ylabel("Average popularity score")
ax.set_ylim(0, 85)
ax.spines[["top", "right"]].set_visible(False)
ax.grid(axis="y", color=GRID, linewidth=0.8)
ax.set_axisbelow(True)
plt.tight_layout()
plt.savefig(OUT / "chart_popularity_by_artist_type.png", dpi=200)
plt.close()

print("Saved 4 charts to", OUT)
