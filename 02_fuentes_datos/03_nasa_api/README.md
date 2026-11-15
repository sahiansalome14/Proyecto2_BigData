# 03. Fuente de datos: NASA Exoplanet Archive TAP (URL / API)

## 1. Descripción de la fuente

La tercera fuente de datos del proyecto consiste en una **interfaz de programación de aplicaciones (API)** pública que permite consultar dinámicamente parámetros físicos y orbitales de los exoplanetas confirmados.

Se utiliza el servicio **Table Access Protocol (TAP)** del [NASA Exoplanet Archive](https://exoplanetarchive.ipac.caltech.edu/), operado por el California Institute of Technology (Caltech) e IPAC bajo contrato con la NASA.

Esta fuente complementa la información del catálogo almacenado en EC2 y de las estrellas almacenadas en RDS MariaDB, aportando variables críticas para responder las preguntas de negocio:
- El **radio del planeta** (`pl_rade`), necesario para la clasificación por tamaños (Tierra, Super-Tierra, Subneptuniano, Neptuniano, Gigante gaseoso).
- La **masa del planeta** (`pl_bmasse`), para estudiar la relación masa-radio.
- El **periodo orbital** (`pl_orbper`), para determinar los planetas con órbitas más cortas.

---

## 2. Protocolo y especificación técnica de la API

- **Estándar:** IVOA Table Access Protocol (TAP) v1.0.
- **Lenguaje de consulta:** ADQL (Astronomical Data Query Language), un dialecto estándar basado en SQL-92.
- **Endpoint sincrónico:** `https://exoplanetarchive.ipac.caltech.edu/TAP/sync`
- **Método HTTP:** `GET` / `POST`
- **Tabla consultada:** `ps` (*Planetary Systems Composite Parameters*).
- **Formatos de respuesta soportados:** `json`, `csv`, `votable`.

---

## 3. Consulta ADQL diseñada

Para asegurar la consistencia de los datos y evitar registros redundantes, se utiliza la siguiente consulta:

```sql
SELECT pl_name, pl_rade, pl_bmasse, pl_orbper
FROM ps
WHERE default_flag = 1
  AND pl_name IS NOT NULL
ORDER BY pl_name
```

### Justificación de filtros y campos:

| Campo / Filtro | Propósito |
|---|---|
| `pl_name` | Identificador único del planeta. Clave primaria lógica para cruzar con el catálogo CSV de EC2. |
| `pl_rade` | Radio del planeta en radios terrestres ($R_\oplus$). Base de la clasificación de tamaño. |
| `pl_bmasse` | Masa del planeta expresada en masas terrestres ($M_\oplus$). |
| `pl_orbper` | Periodo orbital en días terrestres. |
| `WHERE default_flag = 1` | Garantiza que se extraiga el conjunto de parámetros de referencia oficial seleccionado por la NASA para cada planeta (evita duplicados de publicaciones múltiples). |
| `ORDER BY pl_name` | Asegura consistencia y reproducibilidad en la ordenación de los datos. |

---

## 4. Script de extracción: `extract_api.py`

Se implementó el script `extract_api.py` en Python 3 para consultar la API de forma automatizada, validar las respuestas HTTP, presentar estadísticas del conjunto descargado y almacenar el resultado en disco.

### 4.1. Instalación de dependencias

```bash
pip install -r requirements.txt
```

### 4.2. Opciones de ejecución

El script soporta argumentos mediante línea de comandos:

```bash
# Extracción completa en formato JSON (por defecto)
python extract_api.py

# Extracción completa en formato CSV
python extract_api.py --format csv

# Extracción con ruta de salida personalizada
python extract_api.py --format json --output ./datos/exoplanetas_api.json

# Extracción de prueba con límite de registros
python extract_api.py --format json --limit 10
```

---

## 5. Salida esperada y formato de datos

Al ejecutar el script en formato JSON, se genera un archivo estructurado con el siguiente formato:

```json
[
  {
    "pl_name": "11 Com b",
    "pl_rade": null,
    "pl_bmasse": 6165.6,
    "pl_orbper": 326.03
  },
  {
    "pl_name": "11 UMi b",
    "pl_rade": null,
    "pl_bmasse": 4684.81,
    "pl_orbper": 516.21997
  },
  {
    "pl_name": "14 And b",
    "pl_rade": null,
    "pl_bmasse": 1525.5,
    "pl_orbper": 185.84
  },
  {
    "pl_name": "Kepler-186 f",
    "pl_rade": 1.17,
    "pl_bmasse": 1.71,
    "pl_orbper": 129.9441
  }
]
```

### Resumen estadístico reportado en consola:

```text
============================================================
         RESUMEN DE EXTRACCIÓN - API NASA TAP
============================================================
Total de exoplanetas extraídos:      5,700+
Planetas con Radio (pl_rade):       4,500+ (78.9%)
Planetas con Masa (pl_bmasse):      2,400+ (42.1%)
Planetas con Periodo (pl_orbper):   5,600+ (98.2%)
============================================================
```

> **Nota astronómica:** En astronomía de exoplanetas, no todos los métodos de detección permiten medir simultáneamente la masa y el radio. El método de Tránsito mide el radio, mientras que la Velocidad Radial mide la masa mínima. En la etapa de limpieza y transformación con Spark (Punto 4) se gestionarán los valores nulos mediante imputación o filtrado según la pregunta de negocio.

---

