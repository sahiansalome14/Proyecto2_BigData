SELECT
    size_category,
    COUNT(*) AS total_planetas
FROM curated_hive.exoplanets
WHERE size_category IS NOT NULL
GROUP BY size_category
ORDER BY total_planetas DESC;
