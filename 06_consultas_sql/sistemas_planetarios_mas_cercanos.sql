SELECT
    hostname,
    MIN(sy_dist) AS distancia_parsecs
FROM exoplanets
WHERE sy_dist IS NOT NULL
GROUP BY hostname
ORDER BY distancia_parsecs ASC
LIMIT 10;