"""
Exploratory statistical analysis — Spotify Top 100 Songs 2010-2019.

Goals:
1. Recompute (and validate) the audio-feature correlations noted in the
   original project (energy/loudness, danceability/valence, speechiness/pop).
2. Identify which audio features correlate most with `popularity`.
3. Fit a lightweight linear regression as a first-pass "what predicts
   popularity" model — deliberately simple (interpretable coefficients,
   not a black box), consistent with a "little bit of Python" scope.
4. Export correlation matrix + regression summary as CSV/JSON for the
   report and the dashboard.

Run: python3 04_analysis.py
"""

import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error
import json

df = pd.read_csv("../data/spotify_clean.csv")

FEATURES = ["tempo_bpm", "energy", "danceability", "loudness_db", "liveness",
            "valence", "duration_sec", "acousticness", "speechiness"]

# ---------------------------------------------------------------------------
# 1. Correlation matrix
# ---------------------------------------------------------------------------
corr = df[FEATURES + ["popularity"]].corr(method="pearson").round(3)
corr.to_csv("../data/query_results/correlation_matrix.csv")

print("=== Key correlations (validating the original project's findings) ===")
print(f"energy vs loudness_db:      {corr.loc['energy', 'loudness_db']}")
print(f"danceability vs valence:    {corr.loc['danceability', 'valence']}")
print(f"speechiness vs popularity:  {corr.loc['speechiness', 'popularity']}")

print("\n=== Features most correlated with popularity ===")
pop_corr = corr["popularity"].drop("popularity").sort_values(key=abs, ascending=False)
print(pop_corr)

# ---------------------------------------------------------------------------
# 2. Simple, interpretable linear regression: predict popularity from
#    audio features. Not meant to be a strong predictive model — the point
#    is to quantify direction/magnitude of each feature's association with
#    popularity in a way that's easy to explain in an interview.
# ---------------------------------------------------------------------------
X = df[FEATURES]
y = df["popularity"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = LinearRegression()
model.fit(X_train, y_train)
y_pred = model.predict(X_test)

r2 = r2_score(y_test, y_pred)
mae = mean_absolute_error(y_test, y_pred)

coefs = pd.Series(model.coef_, index=FEATURES).sort_values(key=abs, ascending=False)

print(f"\n=== Linear regression: popularity ~ audio features ===")
print(f"R^2 on holdout set: {r2:.3f}")
print(f"MAE on holdout set: {mae:.2f} popularity points")
print("\nStandardized-scale coefficients (direction & relative weight):")
print(coefs)

results = {
    "r2": round(r2, 3),
    "mae": round(mae, 2),
    "coefficients": coefs.round(3).to_dict(),
    "top_correlations_with_popularity": pop_corr.round(3).to_dict(),
    "validated_findings": {
        "energy_vs_loudness": float(corr.loc["energy", "loudness_db"]),
        "danceability_vs_valence": float(corr.loc["danceability", "valence"]),
        "speechiness_vs_popularity": float(corr.loc["speechiness", "popularity"]),
    },
}
with open("../data/query_results/regression_summary.json", "w") as f:
    json.dump(results, f, indent=2)

print("\nSaved correlation_matrix.csv and regression_summary.json")
