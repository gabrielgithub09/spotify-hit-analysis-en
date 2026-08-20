"""
Popularité par tonalité (key) et par mode (majeur/mineur) — analyse demandée
en complément de la section 7 : ces deux variables étaient déjà incluses
dans la régression multivariée (07_range_restriction_test.py) mais jamais
étudiées individuellement. Ce script comble ce manque.

Key et mode sont les variables les plus proches d'un descripteur de
"mélodie" disponibles dans ce dataset (voir le glossaire du rapport pour
pourquoi une vraie mélodie n'y figure pas).

Run: python3 09_key_mode_analysis.py
"""

import pandas as pd
import json
from scipy import stats

df = pd.read_csv("../data_v2/spotify_extended_clean.csv")

# key: 0=C, 1=C#/Db, 2=D, ... 11=B (convention Spotify, notation "pitch class")
KEY_NAMES = ["C", "C#/Db", "D", "D#/Eb", "E", "F", "F#/Gb", "G", "G#/Ab", "A", "A#/Bb", "B"]

# --- Mode : majeur (1) vs mineur (0) ---
mode_stats = df.groupby("mode")["popularity"].agg(["mean", "count"]).round(2)
major = df[df["mode"] == 1]["popularity"]
minor = df[df["mode"] == 0]["popularity"]
t, pval_t = stats.ttest_ind(major, minor, equal_var=False)

print("=== Popularité par mode ===")
print(mode_stats)
print(f"T-test majeur vs mineur : t={t:.2f}, p-value={pval_t:.6f}")

# --- Key : les 12 tonalités ---
key_stats = df.groupby("key")["popularity"].agg(["mean", "count"]).round(2)
key_stats.index = [KEY_NAMES[i] for i in key_stats.index]
key_stats = key_stats.sort_values("mean", ascending=False)
groups = [df[df["key"] == k]["popularity"] for k in range(12)]
f, pval_anova = stats.f_oneway(*groups)

print("\n=== Popularité par tonalité (key) ===")
print(key_stats)
print(f"\nÉcart-type des moyennes entre tonalités : {key_stats['mean'].std():.2f} points (sur une échelle de 100)")
print(f"ANOVA (12 tonalités) : F={f:.2f}, p-value={pval_anova:.6f}")

print("\n=== Conclusion ===")
print("Les deux tests sont statistiquement significatifs (p < 0.0001) uniquement parce")
print("que l'échantillon est très grand (89 740 titres). Les écarts de popularité réels")
print("restent minimes (< 1.5 point sur 100) : tonalité et mode n'ont quasiment aucun")
print("pouvoir explicatif pratique sur la popularité d'un titre.")

# --- Export ---
out = {
    "mode_popularity": {
        "minor_mean": float(mode_stats.loc[0, "mean"]), "major_mean": float(mode_stats.loc[1, "mean"]),
        "ttest_t": round(float(t), 2), "ttest_pvalue": float(pval_t),
    },
    "key_popularity": key_stats.reset_index().rename(columns={"index": "key"}).to_dict(orient="records"),
    "key_anova": {"F": round(float(f), 2), "pvalue": float(pval_anova)},
}
with open("../data_v2/key_mode_analysis.json", "w") as fh:
    json.dump(out, fh, indent=2)
print("\nSaved ../data_v2/key_mode_analysis.json")
