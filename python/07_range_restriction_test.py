"""
Core test: does a larger, unrestricted dataset change the original project's
conclusions? Three things to check:

1. Range-restriction hypothesis — recompute correlations/R^2 on the FULL
   popularity range (0-100, hits and flops) vs. a HITS-ONLY subset
   (popularity >= 70, mirroring the original Top-100-only dataset). If R^2
   is much higher on the full range, the original weak result was partly an
   artifact of only ever looking at already-popular songs.
2. New variables — explicit (real flag this time, not a speechiness proxy),
   instrumentalness, key, mode, time_signature — added to the regression.
3. Hit vs. non-hit classification — a simpler, more forgiving question than
   "predict the exact popularity score": can audio features tell a hit
   (popularity >= 70) apart from a random track at all?

Run: python3 07_range_restriction_test.py
"""

import pandas as pd
import numpy as np
import json
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error, roc_auc_score, accuracy_score
from sklearn.preprocessing import StandardScaler

df = pd.read_csv("../data_v2/spotify_extended_clean.csv")

FEATURES = ["danceability", "energy", "loudness", "speechiness", "acousticness",
            "instrumentalness", "liveness", "valence", "tempo"]
NEW_FEATURES = ["explicit", "key", "mode", "time_signature"]
ALL_FEATURES = FEATURES + NEW_FEATURES

results = {}

# ---------------------------------------------------------------------------
# 1. Range-restriction test: full range vs hits-only subset
# ---------------------------------------------------------------------------
def fit_and_score(data, features, label):
    X = data[features].copy()
    if "explicit" in X.columns:
        X["explicit"] = X["explicit"].astype(int)
    y = data["popularity"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = LinearRegression().fit(X_train, y_train)
    y_pred = model.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    coefs = pd.Series(model.coef_, index=features).sort_values(key=abs, ascending=False)
    print(f"\n=== {label} (n={len(data)}) ===")
    print(f"Popularity: mean={data['popularity'].mean():.1f}, std={data['popularity'].std():.1f}, range={data['popularity'].min()}-{data['popularity'].max()}")
    print(f"R^2 = {r2:.3f}  |  MAE = {mae:.2f}")
    print("Top coefficients:", coefs.head(4).round(2).to_dict())
    return {"n": len(data), "pop_mean": round(data["popularity"].mean(),1), "pop_std": round(data["popularity"].std(),1),
            "r2": round(r2, 3), "mae": round(mae, 2), "coefficients": coefs.round(3).to_dict()}

full_result = fit_and_score(df, FEATURES, "FULL RANGE (0-100 popularity, hits + flops)")
hits_only = df[df["popularity"] >= 70]
hits_result = fit_and_score(hits_only, FEATURES, "HITS-ONLY SUBSET (popularity >= 70, mirrors original project)")

# Original Top-100 (2010-2019) project result, for the 3-way comparison table
original_result = {"n": 1000, "pop_mean": 74.8, "pop_std": None, "r2": 0.060, "mae": 6.28}

results["range_restriction_test"] = {
    "original_top100_only": original_result,
    "extended_hits_only_70plus": hits_result,
    "extended_full_range": full_result,
}

print("\n" + "="*70)
print("RANGE-RESTRICTION TEST — SUMMARY")
print("="*70)
print(f"Original Top-100 dataset (popularity ~60-100): R^2 = {original_result['r2']}")
print(f"Extended dataset, hits-only subset (popularity >= 70): R^2 = {hits_result['r2']}")
print(f"Extended dataset, FULL range (popularity 0-100): R^2 = {full_result['r2']}")
print("-> Confirms the range-restriction hypothesis" if full_result['r2'] > hits_result['r2'] * 2 else "-> Does NOT clearly confirm the range-restriction hypothesis")

# ---------------------------------------------------------------------------
# 2. Extended regression with new variables (full range)
# ---------------------------------------------------------------------------
X = df[ALL_FEATURES].copy()
X["explicit"] = X["explicit"].astype(int)
y = df["popularity"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
model_ext = LinearRegression().fit(X_train, y_train)
y_pred = model_ext.predict(X_test)
r2_ext = r2_score(y_test, y_pred)
coefs_ext = pd.Series(model_ext.coef_, index=ALL_FEATURES).sort_values(key=abs, ascending=False)
print(f"\n=== FULL RANGE + new variables (explicit, key, mode, time_signature) ===")
print(f"R^2 = {r2_ext:.3f} (vs {full_result['r2']} without the new variables)")
print(coefs_ext.round(3))

results["extended_regression_with_new_vars"] = {
    "r2": round(r2_ext, 3),
    "r2_gain_vs_audio_only": round(r2_ext - full_result["r2"], 3),
    "coefficients": coefs_ext.round(3).to_dict(),
}

# Explicit content vs popularity — direct comparison (real flag this time)
pop_explicit = df[df["explicit"]]["popularity"].mean()
pop_clean = df[~df["explicit"]]["popularity"].mean()
print(f"\nAvg popularity — explicit tracks: {pop_explicit:.1f} | non-explicit: {pop_clean:.1f}")
results["explicit_vs_popularity"] = {"explicit_avg": round(pop_explicit,1), "clean_avg": round(pop_clean,1)}

# ---------------------------------------------------------------------------
# 3. Hit vs non-hit classification (logistic regression)
# ---------------------------------------------------------------------------
X = df[FEATURES]
y = df["is_hit"].astype(int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
scaler = StandardScaler().fit(X_train)
clf = LogisticRegression(max_iter=1000, class_weight="balanced").fit(scaler.transform(X_train), y_train)
y_proba = clf.predict_proba(scaler.transform(X_test))[:, 1]
y_pred_cls = clf.predict(scaler.transform(X_test))
auc = roc_auc_score(y_test, y_proba)
acc = accuracy_score(y_test, y_pred_cls)
clf_coefs = pd.Series(clf.coef_[0], index=FEATURES).sort_values(key=abs, ascending=False)

print(f"\n=== Hit (popularity>=70) vs non-hit classifier (logistic regression) ===")
print(f"AUC = {auc:.3f}  |  Accuracy = {acc:.3f}  |  Base rate (hits) = {y.mean():.3f}")
print("Top coefficients:", clf_coefs.round(2).to_dict())

results["hit_classifier"] = {
    "auc": round(auc, 3), "accuracy": round(acc, 3), "base_rate": round(y.mean(), 3),
    "coefficients": clf_coefs.round(3).to_dict(),
}

# ---------------------------------------------------------------------------
# 4. Genre-level popularity, unrestricted by chart eligibility (macro genres)
# ---------------------------------------------------------------------------
genre_pop = df.groupby("macro_genre")["popularity"].agg(["mean", "count"]).round(1).sort_values("mean", ascending=False)
print(f"\n=== Popularity by macro-genre (full catalog, {df['macro_genre'].nunique()} buckets) ===")
print(genre_pop)
results["genre_popularity"] = genre_pop.reset_index().to_dict(orient="records")

with open("../data_v2/extended_analysis_results.json", "w") as f:
    json.dump(results, f, indent=2)

print("\nSaved ../data_v2/extended_analysis_results.json")
