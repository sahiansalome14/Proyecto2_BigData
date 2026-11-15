## Variables principales del análisis

Para realizar el análisis de los exoplanetas se seleccionarán variables que permitan estudiar sus características físicas, orbitales y los sistemas planetarios a los que pertenecen.

Estas variables facilitarán la integración de las diferentes fuentes de datos, la clasificación de los planetas y la identificación de patrones relevantes.

| Variable | Descripción | Unidad |
|---|---|---|
| `pl_name` | Nombre del exoplaneta | — |
| `hostname` | Nombre de la estrella anfitriona | — |
| `pl_rade` | Radio del planeta | Radios terrestres |
| `pl_bmasse` | Masa del planeta | Masas terrestres |
| `pl_orbper` | Periodo orbital | Días |
| `sy_dist` | Distancia del sistema planetario respecto a la Tierra | Parsecs |
| `sy_pnum` | Cantidad de planetas confirmados en el sistema | Planetas |
| `discoverymethod` | Método utilizado para descubrir el planeta | — |
| `disc_year` | Año del descubrimiento | Año |

## Procesamiento y análisis esperado

Una vez integrados los datos provenientes de las tres fuentes, se realizará un proceso de preparación y análisis con el propósito de garantizar la calidad de la información e identificar patrones en las características de los exoplanetas.

Las principales operaciones contempladas son:

1. **Limpieza de datos:** eliminar registros duplicados e identificar valores faltantes o inconsistentes.
2. **Estandarización:** normalizar los nombres de las estrellas y los planetas para facilitar la integración de las fuentes.
3. **Clasificación:** agrupar los exoplanetas según sus categorías de tamaño, utilizando el radio expresado en radios terrestres.
4. **Agrupación:** organizar los planetas por estrella anfitriona para identificar las características de cada sistema planetario.
5. **Análisis estadístico:** calcular promedios, cantidades y distribuciones de las variables seleccionadas.
6. **Identificación de sistemas destacados:** determinar cuáles tienen mayor cantidad de planetas y cuáles se encuentran a menor distancia de la Tierra.
7. **Análisis de características físicas:** estudiar la relación entre la masa y el radio de los exoplanetas.
8. **Análisis orbital:** comparar los periodos orbitales para identificar los planetas que completan sus órbitas en menor tiempo.

Los resultados de este procesamiento permitirán responder las preguntas de negocio planteadas y construir visualizaciones que faciliten la exploración, interpretación y comparación de los diferentes sistemas planetarios.