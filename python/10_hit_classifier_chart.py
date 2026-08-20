"""
Static chart for the Word report: standardized coefficients of the hit /
non-hit logistic regression (section 7.3), built with matplotlib using the
project's validated palette. Blue = positive coefficient (associated with a
higher chance of being a hit), red = negative (associated with a lower
chance) — same diverging convention as the interactive HTML dashboard.

Run: python3 10_hit_classifier_chart.py
"""

import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

OUT = Path("../docs/assets_v2")
OUT.mkdir(parents=True, exist_ok=True)

# Palette (see dataviz skill reference palette) — diverging pair, positive = blue
BLUE = "#2a78d6"
RED = "#e34948"
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

coef = results["hit_classifier"]["coefficients"]
auc = results["hit_classifier"]["auc"]

# Already ordered by |value| descending in the source JSON; keep that order,
# reversed for barh (largest at top).
items = list(coef.items())[::-1]
labels = [k for k, _ in items]
values = [v for _, v in items]
colors = [BLUE if v >= 0 else RED for v in values]

fig, ax = plt.subplots(figsize=(8.2, 4.8))
bars = ax.barh(labels, values, color=colors, height=0.6)
for b, v in zip(bars, values):
    x = v + (0.02 if v >= 0 else -0.02)
    ha = "left" if v >= 0 else "right"
    ax.text(x, b.get_y() + b.get_height() / 2, f"{v:.2f}", va="center", ha=ha, fontsize=9, color=INK_SECONDARY)

ax.axvline(0, color=MUTED, linewidth=0.8)
ax.set_xlim(-1.0, 1.0)
ax.set_title(
    f'What distinguishes a "hit" (popularity >= 70) from the rest of the catalog\n'
    f"Standardized coefficients, logistic regression, AUC = {auc}",
    fontsize=12.5, color=INK, loc="left", pad=14,
)
ax.spines[["top", "right", "left"]].set_visible(False)
ax.grid(axis="x", color=GRID, linewidth=0.8)
ax.set_axisbelow(True)
plt.tight_layout()
plt.savefig(OUT / "chart_hit_classifier.png", dpi=200)
plt.close()

print("Saved", OUT / "chart_hit_classifier.png")
