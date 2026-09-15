# Spotify Top 100 Songs (2010-2019): Analysis for a Record Label

Personal project, out of interest in data analysis applied to music: SQL, Python, Power BI (see `powerbi/`), plus an interactive HTML/CSS/JavaScript dashboard.

**Business question:** what characteristics make a song popular?

**Interactive dashboard online:** [gabrielgithub09.github.io/spotify-hit-analysis-en/dashboard/spotify_dashboard.html](https://gabrielgithub09.github.io/spotify-hit-analysis-en/dashboard/spotify_dashboard.html)

## Repo structure

```
data/
  spotify_raw.xlsx          source file (Kaggle, enriched)
  spotify_clean.csv         cleaned dataset (1000 rows x 23 columns)
  spotify.db                SQLite database, star schema
  query_results/            results of the 11 SQL queries + correlation matrix

data_v2/
  spotify_extended_clean.csv     cleaned extended dataset (89,740 unique tracks, hits + flops, popularity 0-100)
  spotify_extended.db            corresponding SQLite database
  extended_analysis_results.json regression/classification results (report section 7)
  key_mode_analysis.json         key/mode analysis results (appendix)
  query_results/                 results of the 5 extended SQL queries
  track_genre_long.csv           long table track <-> micro-genre (before deduplication)

python/
  01_clean_data.py            cleaning & feature engineering (original dataset)
  02_build_db.py              building the SQLite star schema (original dataset)
  03_run_queries.py           running + exporting SQL queries (original dataset)
  04_analysis.py               correlations + linear regression (original dataset)
  05_charts.py                 static charts (matplotlib) for the report
  06_clean_extended.py         cleaning the extended dataset (89,740 tracks)
  07_range_restriction_test.py range-restriction hypothesis test + hit/non-hit classification
  08_build_extended_db.py      SQLite database + queries on the extended dataset
  09_key_mode_analysis.py      supplementary key/mode analysis
  10_hit_classifier_chart.py   static hit/non-hit classifier chart for the report
  11_r2_comparison_chart.py    static R² comparison chart for the report
  12_genre_popularity_chart.py static genre-popularity chart for the report

sql/
  analysis_queries.sql          11 queries on the original dataset (CTEs, window functions, joins)
  extended_analysis_queries.sql 5 queries on the extended dataset (RANK, aggregations, justified denormalization)

dashboard/
  spotify_dashboard.html    standalone interactive dashboard (open in a browser, or online via GitHub Pages)

powerbi/
  spotify_dashboard.pbix       Power BI Desktop file (same star schema, DAX measures, 4 report pages)
  Spotify_PowerBI_Export.pdf   static PDF export of the 4 report pages (Overview, Evolution over time, Artists, What explains popularity)

docs/
  Spotify_Project_Report.pdf   full report (methodology, insights, glossary, section 7 = extension)
  assets/, assets_v2/       charts used in the report
```

## Reproducing the analysis

```bash
cd python
# Original dataset (1000 tracks, Top 100 2010-2019)
python3 01_clean_data.py    # -> data/spotify_clean.csv
python3 02_build_db.py      # -> data/spotify.db
python3 03_run_queries.py   # -> data/query_results/*.csv
python3 04_analysis.py      # -> correlations + regression
python3 05_charts.py        # -> docs/assets/*.png

# Extended dataset (89,740 tracks, hits + flops), robustness test
python3 06_clean_extended.py            # -> data_v2/spotify_extended_clean.csv
python3 07_range_restriction_test.py    # -> data_v2/extended_analysis_results.json
python3 08_build_extended_db.py         # -> data_v2/spotify_extended.db + SQL queries
python3 09_key_mode_analysis.py         # -> data_v2/key_mode_analysis.json
python3 10_hit_classifier_chart.py      # -> docs/assets_v2/chart_hit_classifier.png
python3 11_r2_comparison_chart.py       # -> docs/assets_v2/chart_r2_comparison.png
python3 12_genre_popularity_chart.py    # -> docs/assets_v2/chart_genre_popularity_full.png
```

The dashboard opens directly (`dashboard/spotify_dashboard.html`), no installation required. The Power BI file (`powerbi/spotify_dashboard.pbix`) requires the free Power BI Desktop to open and explore interactively; a static PDF export is provided as well for a quick look without installing anything.

## Main result

Audio characteristics alone explain very little of a track's popularity (R² = 0.06 on the Top 100, 1000 tracks). Retested on a second, independent dataset of 89,740 tracks (hits and flops combined): R² remains just as low (0.028); the conclusion is confirmed, not overturned, by sample size. This second dataset does, however, make it possible to calculate a hit-conversion rate by genre, which is impossible to obtain without data that includes flops (hip-hop/r&b: 10.5%; electronic/dance, the highest-volume genre: only 3.5%). Details in `docs/Spotify_Project_Report.pdf`, section 7.

Data sources:
- [Kaggle: Top Spotify songs from 2010-2019 by year](https://www.kaggle.com/datasets/leonardopena/top-spotify-songs-from-20102019-by-year/data)
- [Kaggle: Spotify Tracks Dataset (maharshipandya, 114k tracks)](https://www.kaggle.com/datasets/maharshipandya/-spotify-tracks-dataset)
