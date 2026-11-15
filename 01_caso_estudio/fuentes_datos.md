## Fuentes de datos

Para el desarrollo del caso de estudio se utilizarán tres fuentes de datos de diferente naturaleza: una base de datos relacional, archivos CSV y una API pública. Esta combinación permitirá integrar información proveniente de distintos medios y construir un proceso de ingesta y análisis dentro de AWS.

### Descripción general de las fuentes

| Tipo de fuente | Tecnología | Información almacenada |
|---|---|---|
| Base de datos | AWS RDS MariaDB | Información de estrellas anfitrionas y sistemas planetarios. |
| Archivos | Archivos CSV almacenados en una instancia EC2 | Catálogo de exoplanetas confirmados. |
| URL / API | NASA Exoplanet Archive TAP | Parámetros físicos y orbitales de los exoplanetas. |

### 1. Base de datos: AWS RDS MariaDB

Se utilizará **Amazon RDS con MariaDB** para almacenar información estructurada sobre las estrellas anfitrionas y los sistemas planetarios. Se diseñará un modelo relacional con tablas relacionadas que permitan vincular cada estrella con sus respectivos sistemas y planetas.

Esta fuente permitirá simular el acceso a datos provenientes de una base de datos relacional y realizar su posterior extracción hacia el Data Lake en Amazon S3.

### 2. Archivos: CSV almacenados en una instancia EC2

Se utilizarán archivos en formato **CSV**, descargados del NASA Exoplanet Archive, que contendrán información del catálogo de exoplanetas confirmados.

Los archivos se almacenarán en una instancia de **Amazon EC2**, que funcionará como fuente de datos basada en archivos. Desde esta instancia se realizará la extracción automática de la información para su posterior almacenamiento en el Data Lake de Amazon S3.

### 3. URL / API: NASA Exoplanet Archive TAP

Se utilizará la API pública **Table Access Protocol (TAP)** del NASA Exoplanet Archive para consultar información complementaria de los exoplanetas mediante solicitudes HTTP.

A través de consultas utilizando el lenguaje ADQL (Astronomical Data Query Language), se obtendrán parámetros como la masa, el radio, el periodo orbital, la distancia respecto a la Tierra y el año de descubrimiento.

Esta fuente permitirá incorporar datos directamente desde un servicio web externo y automatizar su consulta como parte del proceso de ingesta.

**Referencias oficiales:**

- NASA Exoplanet Archive: https://exoplanetarchive.ipac.caltech.edu/
- Documentación de la API TAP: https://exoplanetarchive.ipac.caltech.edu/docs/TAP/usingTAP.html