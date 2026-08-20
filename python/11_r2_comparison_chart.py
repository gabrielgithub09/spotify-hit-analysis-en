"""
Static chart for the Word report (section 7.2): R^2 of the popularity ~
audio-features regression, compared across the original dataset and the two
extended-dataset subsets. Built with matplotlib using the project's
validated palette.

Run: python3 11_r2_comparison_chart.py
"""

import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

OUT = Path("../docs/assets_v2")
OUT.mkdir(parents=True, exist_ok=True)

BLUE = "#2a78d6"
ORANGE = "#eb6834"
GRAY_MID = "#a8a6a0"
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

rrt = results["range_restriction_test"]
labels = ["Original\n(Top 100, n=1000)", "Extended, hits only\n(pop >= 70, n=3126)", "Extended, full range\n(n=89740)"]
values = [rrt["original_top100_only"]["r2"], rrt["extended_hits_only_70plus"]["r2"], rrt["extended_full_range"]["r2"]]
colors = [GRAY_MID, ORANGE, BLUE]

fig, ax = plt.subplots(figsize=(7.0, 4.595))
bars = ax.bar(labels, values, color=colors, width=0.55)
for b, v in zip(bars, values):
    ax.text(b.get_x() + b.get_width() / 2, v + 0.002, f"{v:.3f}", ha="center", va="bottom", fontsize=10, fontweight="bold", color=INK)

ax.set_ylim(0, 0.08)
ax.set_ylabel("R² (share of variance explained)")
ax.set_title("R² of the popularity ~ audio features regression,\nby dataset and subset tested", fontsize=12.5, loc="left", pad=14, color=INK)
ax.spines[["top", "right"]].set_visible(False)
ax.grid(axis="y", color=GRID, linewidth=0.8)
ax.set_axisbelow(True)
plt.tight_layout()
plt.savefig(OUT / "chart_r2_comparison.png", dpi=200)
plt.close()

print("Saved", OUT / "chart_r2_comparison.png")
