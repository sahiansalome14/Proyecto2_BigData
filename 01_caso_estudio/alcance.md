# Alcance del proyecto

## Alcance

El proyecto contempla la integración y el análisis de información relacionada con exoplanetas confirmados y sus sistemas planetarios.

Se trabajará con tres tipos de fuentes:

- **Base de datos:** Amazon RDS con MariaDB, para almacenar información estructurada de estrellas y sistemas planetarios.
- **Archivos:** conjuntos de datos en formato CSV almacenados en una instancia Amazon EC2.
- **URL/API:** NASA Exoplanet Archive, mediante su servicio TAP, para consultar información astronómica.

Los datos serán centralizados en Amazon S3 y organizados en zonas de almacenamiento Raw, Trusted y Gold.

Posteriormente, se realizarán procesos de limpieza, transformación, catalogación y análisis mediante servicios de AWS y herramientas de procesamiento distribuido.

Los resultados se presentarán mediante consultas SQL, análisis con PySpark y una aplicación interactiva desarrollada con Streamlit.

## Delimitaciones

- El estudio se centrará en exoplanetas confirmados disponibles en las fuentes seleccionadas.
- El análisis utilizará los parámetros físicos y orbitales que estén disponibles y tengan calidad suficiente.
- La clasificación por tamaño será un criterio adoptado para el análisis, no una clasificación universal obligatoria.
- La cercanía se determinará utilizando la distancia registrada para el sistema planetario, expresada en pársecs.
- Tener un tamaño similar al de la Tierra no implica que un exoplaneta sea habitable.
- Los resultados dependerán de la disponibilidad, actualización y calidad de los datos consultados.

## Fuera del alcance

El proyecto no pretende determinar si un exoplaneta alberga vida ni establecer su habitabilidad. Tampoco busca realizar simulaciones físicas de los sistemas planetarios.