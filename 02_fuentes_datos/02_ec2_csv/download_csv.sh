#!/usr/bin/env bash
# Script: download_csv.sh
# Descripción: Descarga el catálogo oficial de exoplanetas confirmados del
#              NASA Exoplanet Archive (TAP API) y lo almacena como archivo CSV
#              en la instancia EC2, simulando la fuente basada en archivos.

set -euo pipefail

# Directorio de destino para los archivos CSV
DATA_DIR="${DATA_DIR:-$HOME/data}"
OUTPUT_FILE="$DATA_DIR/exoplanetas_catalogo.csv"

echo "   Descarga de Catálogo de Exoplanetas Confirmados en EC2        "
echo "[1/4] Creando directorio de datos: $DATA_DIR"
mkdir -p "$DATA_DIR"

# Endpoint oficial de NASA Exoplanet Archive TAP
TAP_URL="https://exoplanetarchive.ipac.caltech.edu/TAP/sync"

# Consulta ADQL: Selecciona las variables clave del catálogo de planetas confirmados
# Variables: pl_name, hostname, discoverymethod, disc_year, disc_facility
QUERY="SELECT pl_name, hostname, discoverymethod, disc_year, disc_facility FROM ps WHERE default_flag = 1 AND pl_name IS NOT NULL ORDER BY pl_name"

echo "[2/4] Consultando NASA Exoplanet Archive TAP..."
echo "      Query: $QUERY"

# Descargar CSV utilizando curl
curl -sS -G "$TAP_URL" \
    --data-urlencode "query=$QUERY" \
    --data-urlencode "format=csv" \
    -o "$OUTPUT_FILE"

echo "[3/4] Validando archivo generado en: $OUTPUT_FILE"

if [ ! -s "$OUTPUT_FILE" ]; then
    echo "ERROR: El archivo descargado está vacío o no se pudo generar."
    exit 1
fi

TOTAL_LINES=$(wc -l < "$OUTPUT_FILE")
FILE_SIZE=$(du -h "$OUTPUT_FILE" | cut -f1)

echo "   Descarga completada exitosamente                              "
echo "Ruta del archivo: $OUTPUT_FILE"
echo "Tamaño en disco:  $FILE_SIZE"
echo "Total de líneas:  $TOTAL_LINES (incluyendo cabecera)"
echo ""
echo "Primeras 5 líneas del catálogo:"
head -n 5 "$OUTPUT_FILE"
echo "..."
echo "Últimas 3 líneas del catálogo:"
tail -n 3 "$OUTPUT_FILE"
