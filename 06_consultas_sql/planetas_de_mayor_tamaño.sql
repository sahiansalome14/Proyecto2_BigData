SELECT
    pl_name,
    hostname,
    pl_rade
FROM exoplanets
WHERE pl_rade IS NOT NULL
ORDER BY pl_rade DESC
LIMIT 10;