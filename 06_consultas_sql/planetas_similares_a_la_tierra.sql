SELECT
    pl_name,
    hostname,
    pl_rade,
    is_earth_similar
FROM exoplanets
WHERE is_earth_similar = TRUE
ORDER BY pl_rade ASC;