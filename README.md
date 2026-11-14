# Análisis de Exoplanetas mediante un Data Lake en AWS

## Descripción del proyecto

Este proyecto desarrolla un caso de estudio orientado a la integración, almacenamiento, procesamiento y análisis de datos astronómicos relacionados con exoplanetas, es decir, planetas que orbitan estrellas diferentes al Sol.

Se utilizarán datos provenientes de tres tipos de fuentes: bases de datos relacionales, archivos y servicios web. Estas fuentes se integrarán en un Data Lake implementado en Amazon Web Services (AWS), donde los datos serán almacenados, transformados y preparados para su análisis.

Mediante herramientas como Amazon S3, Amazon RDS, AWS Glue, Amazon Athena, Amazon EMR y Apache Spark, se busca identificar patrones en las características físicas y orbitales de los exoplanetas, así como comparar los sistemas planetarios según su composición y diversidad de tamaños.

Finalmente, los resultados se presentarán mediante una aplicación interactiva desarrollada con Streamlit.

## Pregunta de negocio

¿Qué características físicas y orbitales tienen los exoplanetas descubiertos y qué sistemas planetarios se destacan por tener varios planetas, diferentes tamaños y estar más cerca de la Tierra?

## Objetivo general

Integrar, procesar y analizar datos de exoplanetas provenientes de diferentes fuentes de información, utilizando servicios de AWS y herramientas de procesamiento distribuido, para identificar patrones en sus características físicas y orbitales, comparar sistemas planetarios y reconocer aquellos que presentan características destacadas.

## Tecnologías y herramientas

| Tecnología | Utilización |
|---|---|
| Amazon RDS (MariaDB) | Almacenamiento de información estructurada. |
| Amazon EC2 | Almacenamiento y disponibilidad de archivos de datos. |
| NASA Exoplanet Archive API | Obtención de datos astronómicos mediante URL. |
| Amazon S3 | Implementación del Data Lake. |
| AWS Glue | Ingesta, procesamiento y catalogación de datos. |
| Amazon EMR | Procesamiento distribuido y consultas con Hive y Spark. |
| Apache Spark / PySpark | Transformación y análisis de datos. |
| Amazon Athena | Consultas SQL sobre los datos almacenados en S3. |
| API Gateway | Exposición de servicios para la aplicación. |
| Streamlit | Visualización interactiva de resultados. |
| Python y SQL | Desarrollo de scripts, consultas y análisis. |

## Fuentes de datos

El proyecto integra información procedente de las siguientes fuentes:

1. **Base de datos relacional:** Amazon RDS con MariaDB, para almacenar información estructurada de estrellas y sistemas planetarios.
2. **Archivos:** archivos CSV almacenados en una instancia Amazon EC2, con información de exoplanetas.
3. **URL/API:** NASA Exoplanet Archive, para consultar y obtener información complementaria sobre exoplanetas.

Fuente principal: [NASA Exoplanet Archive](https://exoplanetarchive.ipac.caltech.edu/).

## Arquitectura del Data Lake

El almacenamiento de datos se organizará en tres zonas:

- **Raw:** conserva los datos originales provenientes de las diferentes fuentes.
- **Trusted:** contiene los datos limpios, depurados y estandarizados.
- **Gold:** almacena conjuntos de datos preparados para consultas, análisis y visualizaciones.

## Estructura del repositorio

```text
exoplanets-data-lake/
│
├── 01_caso_estudio/
├── 02_fuentes_datos/
├── 03_ingesta_data_lake/
├── 04_procesamiento_spark/
├── 05_catalogacion/
├── 06_consultas_sql/
├── 07_analisis_pyspark/
├── 08_visualizacion_api/
│
├── evidencias/
├── docs/
├── requirements.txt
├── .gitignore
└── README.md
```

## Resultados esperados

- Integración de datos provenientes de bases de datos, archivos y servicios web.
- Implementación de un Data Lake en Amazon S3.
- Procesamiento y transformación de datos mediante AWS Glue y Apache Spark.
- Catalogación de conjuntos de datos para facilitar su consulta.
- Ejecución de consultas SQL utilizando Athena, Hive y SparkSQL.
- Análisis descriptivo de las características de los exoplanetas mediante PySpark.
- Visualización interactiva de los resultados mediante Streamlit.

## Documentación y reproducibilidad

Cada directorio contiene los scripts, consultas, configuraciones y documentación correspondientes a una etapa del proyecto. También se incluirán evidencias de ejecución para facilitar la comprensión y reproducción del proceso.

## Referencias

- [NASA Exoplanet Archive](https://exoplanetarchive.ipac.caltech.edu/)
- [NASA Exoplanet Catalog](https://science.nasa.gov/exoplanets/exoplanet-catalog/)
- [NASA Exoplanet Archive - TAP Documentation](https://exoplanetarchive.ipac.caltech.edu/docs/TAP/usingTAP.html)
- [Kopparapu et al. (2018)](https://asd.gsfc.nasa.gov/luvoir/resources/docs/science/Kopparapu_ApJ_856.pdf)