-- =============================================================================
-- Extended dataset — Spotify Tracks Dataset (89 740 titres, tout le catalogue,
-- popularité 0-100, hits ET flops). Base : spotify_extended.db, table
-- tracks_extended (dénormalisée : macro_genre reste une colonne du fait plutôt
-- qu'une dimension séparée — 12 valeurs seulement, un join n'apporterait rien).
-- =============================================================================


-- -----------------------------------------------------------------------------
-- Q1. Popularité moyenne par macro-genre, sur le catalogue complet
-- (contrairement à l'analyse originale, non biaisée par l'éligibilité au Top 100)
-- -----------------------------------------------------------------------------
SELECT macro_genre, COUNT(*) AS n_tracks, ROUND(AVG(popularity),1) AS avg_popularity
FROM tracks_extended
GROUP BY macro_genre
ORDER BY avg_popularity DESC;


-- -----------------------------------------------------------------------------
-- Q2. Taux de "hit" (popularité >= 70) par macro-genre
-- Question business : quel genre convertit le mieux un titre sorti en hit ?
-- -----------------------------------------------------------------------------
SELECT
    macro_genre,
    COUNT(*) AS n_tracks,
    SUM(is_hit) AS n_hits,
    ROUND(100.0 * SUM(is_hit) / COUNT(*), 2) AS hit_rate_pct
FROM tracks_extended
GROUP BY macro_genre
ORDER BY hit_rate_pct DESC;


-- -----------------------------------------------------------------------------
-- Q3. Contenu explicite vs popularité (flag réel, plus un proxy speechiness)
-- -----------------------------------------------------------------------------
SELECT explicit, COUNT(*) AS n_tracks, ROUND(AVG(popularity),1) AS avg_popularity
FROM tracks_extended
GROUP BY explicit;


-- -----------------------------------------------------------------------------
-- Q4. Profil audio moyen : hits vs non-hits
-- -----------------------------------------------------------------------------
SELECT
    is_hit,
    COUNT(*) AS n_tracks,
    ROUND(AVG(danceability),3) AS avg_danceability,
    ROUND(AVG(energy),3)       AS avg_energy,
    ROUND(AVG(loudness),1)     AS avg_loudness,
    ROUND(AVG(instrumentalness),3) AS avg_instrumentalness,
    ROUND(AVG(acousticness),3)     AS avg_acousticness
FROM tracks_extended
GROUP BY is_hit;


-- -----------------------------------------------------------------------------
-- Q5. Genres où le volume de sortie et le taux de hit divergent le plus
-- (RANK() sur deux critères + comparaison des rangs) — identifie les genres
-- qui "convertissent" bien avec peu de volume (hip-hop/r&b) vs ceux qui
-- publient beaucoup mais convertissent peu (electronic/dance).
-- -----------------------------------------------------------------------------
WITH stats AS (
    SELECT
        macro_genre,
        COUNT(*) AS n_tracks,
        ROUND(100.0 * SUM(is_hit) / COUNT(*), 2) AS hit_rate_pct,
        RANK() OVER (ORDER BY COUNT(*) DESC) AS volume_rank,
        RANK() OVER (ORDER BY 100.0 * SUM(is_hit) / COUNT(*) DESC) AS hitrate_rank
    FROM tracks_extended
    GROUP BY macro_genre
)
SELECT macro_genre, n_tracks, volume_rank, hit_rate_pct, hitrate_rank,
       (volume_rank - hitrate_rank) AS rank_gap
FROM stats
ORDER BY rank_gap DESC;
