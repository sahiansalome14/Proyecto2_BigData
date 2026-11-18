SELECT
    COUNT(*) AS total_planetas,
    AVG(pl_bmasse) AS masa_promedio,
    AVG(pl_rade) AS radio_promedio,
    CORR(pl_bmasse, pl_rade) AS correlacion_masa_radio
FROM exoplanets
WHERE pl_bmasse IS NOT NULL
AND pl_rade IS NOT NULL;