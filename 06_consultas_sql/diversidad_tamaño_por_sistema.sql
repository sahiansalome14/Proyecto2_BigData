SELECT
    hostname,
    COUNT(*) AS total_planetas,
    COUNT(DISTINCT size_category) AS categorias_diferentes
FROM exoplanets
WHERE size_category IS NOT NULL
GROUP BY hostname
HAVING COUNT(DISTINCT size_category) > 1
ORDER BY categorias_diferentes DESC,
         total_planetas DESC
LIMIT 10;