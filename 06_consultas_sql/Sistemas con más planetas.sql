SELECT
    hostname,
    COUNT(*) AS total_planetas
FROM exoplanets
GROUP BY hostname
ORDER BY total_planetas DESC
LIMIT 10;