# Objetivos del proyecto

## Objetivo general

Integrar, procesar y analizar datos de exoplanetas provenientes de diferentes fuentes de información, utilizando servicios de AWS y herramientas de procesamiento distribuido, para identificar patrones en sus características físicas y orbitales, comparar sistemas planetarios y reconocer aquellos que presentan características destacadas.

## Objetivos específicos

1. Definir el caso de estudio e identificar las preguntas de negocio que orientarán el análisis de exoplanetas.
2. Obtener y preparar datos provenientes de una base de datos MariaDB en Amazon RDS, archivos almacenados en Amazon EC2 y la API de NASA Exoplanet Archive.
3. Implementar procesos de ingesta para centralizar la información de las diferentes fuentes en un Data Lake sobre Amazon S3.
4. Limpiar, estandarizar y transformar los datos mediante AWS Glue y Apache Spark.
5. Catalogar los conjuntos de datos utilizando AWS Glue Data Catalog y herramientas de consulta de Amazon EMR.
6. Ejecutar consultas SQL mediante Amazon Athena, Hive y SparkSQL para responder las preguntas de negocio.
7. Realizar análisis descriptivos adicionales utilizando PySpark.
8. Desarrollar una aplicación interactiva con Streamlit para presentar los resultados del análisis, integrando los servicios necesarios mediante API Gateway.