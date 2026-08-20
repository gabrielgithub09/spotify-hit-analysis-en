"""
Static chart for the Word report (section 7.3): average popularity by
macro-genre across the full extended catalog (89,740 tracks, hits and
flops). Built with matplotlib using the project's validated palette.

Run: python3 12_genre_popularity_chart.py
"""

import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

OUT = Path("../docs/assets_v2")
OUT.mkdir(parents=True, exist_ok=True)

BLUE = "#2a78d6"
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

with open("../data_v2/extended_analysis_results.json") as fh:
    results = json.load(fh)

genre_pop = results["genre_popularity"]  # already sorted desc by mean
labels = [g["macro_genre"] for g in genre_pop][::-1]
values = [g["mean"] for g in genre_pop][::-1]

fig, ax = plt.subplots(figsize=(9.0, 5.2))
bars = ax.barh(labels, values, color=BLUE, height=0.65)
for b, v in zip(bars, values):
    ax.text(v + 0.4, b.get_y() + b.get_height() / 2, f"{v:.1f}", va="center", ha="left", fontsize=9, color=INK_SECONDARY)

ax.set_xlim(0, max(values) * 1.15)
ax.set_xlabel("Average popularity (0-100)")
ax.set_title("Average popularity by macro-genre — full catalog (89,740 tracks)", fontsize=12.5, loc="left", pad=14, color=INK)
ax.spines[["top", "right", "left"]].set_visible(False)
ax.grid(axis="x", color=GRID, linewidth=0.8)
ax.set_axisbelow(True)
plt.tight_layout()
plt.savefig(OUT / "chart_genre_popularity_full.png", dpi=200)
plt.close()

print("Saved", OUT / "chart_genre_popularity_full.png")
