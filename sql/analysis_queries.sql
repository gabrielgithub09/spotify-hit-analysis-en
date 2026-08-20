-- =============================================================================
-- Spotify Top 100 Songs (2010-2019) — Analysis Queries
-- Database: spotify.db (SQLite) — star schema: fact_songs, dim_artist, dim_genre
-- =============================================================================


-- -----------------------------------------------------------------------------
-- Q1. Top 10 genres by number of chart appearances (2010-2019)
-- Business question: which genres dominate the charts overall?
-- -----------------------------------------------------------------------------
SELECT
    g.genre_name,
    COUNT(*)                          AS appearances,
    ROUND(AVG(f.popularity), 1)       AS avg_popularity
FROM fact_songs f
JOIN dim_genre g ON g.genre_id = f.genre_id
GROUP BY g.genre_name
ORDER BY appearances DESC
LIMIT 10;


-- -----------------------------------------------------------------------------
-- Q2. Year-over-year evolution of average audio features
-- Business question: is the "sound" of hit songs changing over the decade?
-- Uses a window function (LAG) to compute year-over-year deltas.
-- -----------------------------------------------------------------------------
WITH yearly AS (
    SELECT
        chart_year,
        ROUND(AVG(energy), 1)        AS avg_energy,
        ROUND(AVG(danceability), 1)  AS avg_danceability,
        ROUND(AVG(valence), 1)       AS avg_valence,
        ROUND(AVG(tempo_bpm), 1)     AS avg_bpm
    FROM fact_songs
    GROUP BY chart_year
)
SELECT
    chart_year,
    avg_energy,
    avg_energy - LAG(avg_energy) OVER (ORDER BY chart_year)             AS energy_yoy_change,
    avg_danceability,
    avg_danceability - LAG(avg_danceability) OVER (ORDER BY chart_year) AS danceability_yoy_change,
    avg_valence,
    avg_bpm
FROM yearly
ORDER BY chart_year;


-- -----------------------------------------------------------------------------
-- Q3. Top 3 highest-popularity songs per chart year
-- Business question: what were the flagship hits of each year?
-- Classic "top-N per group" pattern using ROW_NUMBER().
-- -----------------------------------------------------------------------------
WITH ranked AS (
    SELECT
        f.chart_year,
        f.title,
        a.artist_name,
        f.popularity,
        ROW_NUMBER() OVER (PARTITION BY f.chart_year ORDER BY f.popularity DESC) AS rn
    FROM fact_songs f
    JOIN dim_artist a ON a.artist_id = f.artist_id
)
SELECT chart_year, title, artist_name, popularity
FROM ranked
WHERE rn <= 3
ORDER BY chart_year, rn;


-- -----------------------------------------------------------------------------
-- Q4. Artists with the most chart appearances (recurring hitmakers)
-- Business question: which artists most consistently produce hits?
-- -----------------------------------------------------------------------------
SELECT
    a.artist_name,
    a.artist_type,
    COUNT(*)                      AS chart_appearances,
    ROUND(AVG(f.popularity), 1)   AS avg_popularity,
    MIN(f.chart_year)             AS first_year,
    MAX(f.chart_year)             AS last_year
FROM fact_songs f
JOIN dim_artist a ON a.artist_id = f.artist_id
GROUP BY a.artist_name, a.artist_type
HAVING COUNT(*) >= 5
ORDER BY chart_appearances DESC, avg_popularity DESC;


-- -----------------------------------------------------------------------------
-- Q5. Average popularity by artist configuration (Solo / Duo / Trio / Band)
-- Business question: does performing solo vs. as a group correlate with
-- higher popularity? (mirrors a hypothesis from the original 2019 project)
-- -----------------------------------------------------------------------------
SELECT
    a.artist_type,
    COUNT(*)                     AS songs,
    ROUND(AVG(f.popularity), 1)  AS avg_popularity,
    ROUND(AVG(f.danceability),1) AS avg_danceability
FROM fact_songs f
JOIN dim_artist a ON a.artist_id = f.artist_id
GROUP BY a.artist_type
ORDER BY avg_popularity DESC;


-- -----------------------------------------------------------------------------
-- Q6. Songs that charted in more than one year ("recurring hits")
-- Business question: which songs had unusually long chart longevity?
-- -----------------------------------------------------------------------------
SELECT
    f.title,
    a.artist_name,
    COUNT(*)                         AS years_charted,
    GROUP_CONCAT(f.chart_year, ', ') AS chart_years
FROM fact_songs f
JOIN dim_artist a ON a.artist_id = f.artist_id
WHERE f.is_reappearing_hit = 1
GROUP BY f.title, a.artist_name
ORDER BY years_charted DESC, f.title;


-- -----------------------------------------------------------------------------
-- Q7. Popularity by "high speechiness" flag (proxy for explicit/spoken-word)
-- Business question: does more speech-like content correlate with higher
-- popularity, as the original project's exploratory notes suggested?
-- -----------------------------------------------------------------------------
SELECT
    CASE WHEN high_speechiness_flag = 1 THEN 'High speechiness (>33)'
         ELSE 'Normal speechiness (<=33)' END AS speechiness_group,
    COUNT(*)                                   AS songs,
    ROUND(AVG(popularity), 1)                  AS avg_popularity,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM fact_songs), 1) AS pct_of_all_songs
FROM fact_songs
GROUP BY speechiness_group;


-- -----------------------------------------------------------------------------
-- Q8. Popularity tier distribution by genre (top 8 genres only)
-- Business question: which genres reliably produce "Very High" popularity
-- songs vs. genres that just have volume?
-- Uses a CTE to first restrict to the top 8 genres by volume.
-- -----------------------------------------------------------------------------
WITH top_genres AS (
    SELECT genre_id FROM fact_songs
    GROUP BY genre_id
    ORDER BY COUNT(*) DESC
    LIMIT 8
)
SELECT
    g.genre_name,
    f.popularity_tier,
    COUNT(*) AS songs
FROM fact_songs f
JOIN dim_genre g ON g.genre_id = f.genre_id
WHERE f.genre_id IN (SELECT genre_id FROM top_genres)
GROUP BY g.genre_name, f.popularity_tier
ORDER BY g.genre_name,
    CASE f.popularity_tier
        WHEN 'Very High (90+)' THEN 1
        WHEN 'High (75-89)' THEN 2
        WHEN 'Mid (60-74)' THEN 3
        ELSE 4
    END;


-- -----------------------------------------------------------------------------
-- Q9. Danceability vs. valence "feel-good" segment
-- Business question: how big is the share of upbeat, high-energy songs
-- among the most popular tracks? (feeds a Power BI KPI card)
-- -----------------------------------------------------------------------------
SELECT
    COUNT(*)                                                            AS feel_good_songs,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM fact_songs), 1)      AS pct_of_catalog,
    ROUND(AVG(popularity), 1)                                           AS avg_popularity
FROM fact_songs
WHERE danceability >= 70 AND valence >= 60;


-- -----------------------------------------------------------------------------
-- Q10. Genre diversity trend — distinct genres represented per chart year
-- Business question: is the top-100 becoming more or less genre-diverse
-- over time?
-- -----------------------------------------------------------------------------
SELECT
    chart_year,
    COUNT(DISTINCT genre_id) AS distinct_genres,
    COUNT(*)                 AS total_songs
FROM fact_songs
GROUP BY chart_year
ORDER BY chart_year;


-- -----------------------------------------------------------------------------
-- Q11. Each recurring artist's single best (most popular) song
-- Business question: for artists with 5+ hits, what's their signature song?
-- Window function ROW_NUMBER partitioned by artist.
-- -----------------------------------------------------------------------------
WITH artist_counts AS (
    SELECT artist_id, COUNT(*) AS n FROM fact_songs GROUP BY artist_id HAVING n >= 5
),
best_per_artist AS (
    SELECT
        f.artist_id, f.title, f.popularity, f.chart_year,
        ROW_NUMBER() OVER (PARTITION BY f.artist_id ORDER BY f.popularity DESC) AS rn
    FROM fact_songs f
    WHERE f.artist_id IN (SELECT artist_id FROM artist_counts)
)
SELECT a.artist_name, b.title, b.chart_year, b.popularity
FROM best_per_artist b
JOIN dim_artist a ON a.artist_id = b.artist_id
WHERE b.rn = 1
ORDER BY b.popularity DESC;
