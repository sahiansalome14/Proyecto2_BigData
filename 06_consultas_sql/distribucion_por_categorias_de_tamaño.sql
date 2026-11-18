SELECT
    pl_name,
    hostname,
    pl_orbper
FROM exoplanets
WHERE pl_orbper IS NOT NULL
AND pl_orbper > 0
ORDER BY pl_orbper ASC
LIMIT 10;