# Clasificación de exoplanetas por tamaño

## Criterio de clasificación

Para analizar y comparar los exoplanetas se utilizará una clasificación basada en su radio, expresado en radios terrestres (R⊕).

Como referencia se adoptará el esquema de intervalos utilizado en el informe *The Standard Definitions and Evaluation (SDET)* del programa de exploración de exoplanetas de NASA, basado en el trabajo de Kopparapu et al. (2018).

Esta clasificación agrupa los planetas en cinco categorías:

| Categoría | Intervalo de radio |
|---|---:|
| Rocosos | 0.5 ≤ R ≤ 1.0 R⊕ |
| Supertierras | 1.0 < R ≤ 1.75 R⊕ |
| Subneptunianos | 1.75 < R ≤ 3.5 R⊕ |
| Neptunianos | 3.5 < R ≤ 6.0 R⊕ |
| Gigantes tipo Júpiter | 6.0 < R ≤ 14.3 R⊕ |

## Aplicación en el proyecto

Esta clasificación permitirá:

- Agrupar los exoplanetas según su radio.
- Calcular la cantidad de planetas pertenecientes a cada categoría.
- Comparar la diversidad de tamaños entre diferentes sistemas planetarios.
- Construir gráficos y visualizaciones sobre la distribución de tamaños.

Para implementar esta clasificación se utilizará principalmente la variable `pl_rade` del NASA Exoplanet Archive, que representa el radio del planeta expresado en radios terrestres.

Los valores que estén fuera de los intervalos definidos o que no tengan información de radio suficiente se tratarán como no clasificados.

## Consideraciones

Los intervalos corresponden a un esquema de clasificación adoptado para este análisis. No representan una clasificación universal obligatoria para todos los exoplanetas. Además, el radio por sí solo no permite determinar con certeza la composición del planeta ni su habitabilidad.

## Referencias

**Fuente principal:**

NASA Exoplanet Exploration Program. *The Standard Definitions and Evaluation (SDET) Final Report.*

https://exoplanets.nasa.gov/system/internal_resources/details/original/1434_Standards_Team_Final_Report_20191007.pdf

**Artículo científico de referencia:**

Kopparapu et al. (2018). *Exoplanet Classification and Yield Estimates for Direct Imaging Missions.*

https://asd.gsfc.nasa.gov/luvoir/resources/docs/science/Kopparapu_ApJ_856.pdf