# 01. Caso de estudio: Análisis de Exoplanetas

## 1. Contexto

Los exoplanetas son planetas que orbitan estrellas diferentes al Sol. Su estudio permite comprender la diversidad de sistemas planetarios que existen en nuestra galaxia y analizar características como el tamaño, la masa, el periodo orbital y la distancia respecto a la Tierra.

Actualmente, diferentes observatorios y proyectos científicos recopilan grandes cantidades de información sobre estos cuerpos celestes. Una de las fuentes más importantes es NASA Exoplanet Archive, que proporciona información sobre exoplanetas confirmados y sus respectivos sistemas planetarios.

Debido a que la información puede encontrarse distribuida en diferentes fuentes y formatos, este proyecto propone integrar datos provenientes de una base de datos relacional, archivos y una API, para centralizarlos en un Data Lake implementado en AWS.

## 2. Descripción del problema

La información astronómica sobre exoplanetas se encuentra disponible en diferentes fuentes de datos. Para analizarla de manera conjunta, es necesario integrar los registros, estandarizar sus estructuras, eliminar inconsistencias y preparar los datos para realizar consultas y análisis.

El proyecto busca solucionar esta necesidad mediante una arquitectura de procesamiento de datos que permita reunir información de diferentes orígenes y transformarla en conjuntos de datos útiles para el análisis.

## 3. Justificación

El análisis de exoplanetas representa una oportunidad para aplicar conceptos de integración de datos, almacenamiento distribuido y procesamiento de grandes volúmenes de información en un contexto científico.

A través de este caso de estudio se pondrán en práctica tecnologías de computación en la nube y procesamiento distribuido, demostrando cómo los datos provenientes de diferentes fuentes pueden integrarse para responder preguntas relacionadas con las características de los sistemas planetarios.

## 4. Pregunta de negocio

¿Qué características físicas y orbitales tienen los exoplanetas descubiertos y qué sistemas planetarios se destacan por tener varios planetas, diferentes tamaños y estar más cerca de la Tierra?

## 5. Objetivo general

Integrar, procesar y analizar datos de exoplanetas provenientes de diferentes fuentes de información, utilizando servicios de AWS y herramientas de procesamiento distribuido, para identificar patrones en sus características físicas y orbitales, comparar sistemas planetarios y reconocer aquellos que presentan características destacadas.

## 6. Resultados esperados

- Identificar los sistemas planetarios que contienen mayor cantidad de exoplanetas confirmados.
- Reconocer los exoplanetas de mayor y menor tamaño.
- Identificar planetas con radios similares al de la Tierra.
- Comparar los sistemas planetarios según su distancia respecto a la Tierra.
- Analizar la distribución de exoplanetas según sus categorías de tamaño.
- Explorar la relación entre la masa y el radio de los exoplanetas.
- Identificar sistemas planetarios que presentan diversidad de tamaños.

## 7. Herramientas principales

El desarrollo del caso de estudio utilizará servicios de AWS, entre ellos Amazon RDS, Amazon EC2, Amazon S3, AWS Glue, Amazon EMR y Amazon Athena. También se utilizarán Python, Apache Spark, PySpark, SQL y Streamlit.

## 8. Fuente científica principal

NASA Exoplanet Archive: https://exoplanetarchive.ipac.caltech.edu/

Esta plataforma proporciona información sobre exoplanetas confirmados, sus estrellas anfitrionas y diferentes parámetros físicos y orbitales.