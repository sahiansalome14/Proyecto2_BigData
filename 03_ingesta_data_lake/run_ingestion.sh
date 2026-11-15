#!/usr/bin/env bash

# Script: run_ingestion.sh
# Descripción: Ejecuta el pipeline automatizado de ingesta hacia S3 Raw.

set -euo pipefail

# Validar variables de entorno requeridas
if [ -z "${S3_BUCKET:-}" ]; then
    echo "ERROR: Debe definir la variable S3_BUCKET antes de ejecutar."
    echo "Ejemplo: export S3_BUCKET='exoplanets-data-lake-123456789-us-east-1'"
    exit 1
fi

if [ -z "${DB_HOST:-}" ]; then
    echo "ERROR: Debe definir DB_HOST (Endpoint de RDS)."
    exit 1
fi

if [ -z "${DB_PASSWORD:-}" ]; then
    read -s -p "Ingrese la contraseña de MariaDB: " DB_PASSWORD
    echo ""
    export DB_PASSWORD
fi

export DB_USER="${DB_USER:-admin_exoplanets}"
export DB_NAME="${DB_NAME:-exoplanets_db}"
export DB_PORT="${DB_PORT:-3306}"
export DATA_DIR="${DATA_DIR:-$HOME/data}"


echo "   Iniciando Pipeline Automatizado de Ingesta a S3 Raw       "

echo "Bucket S3:   $S3_BUCKET"
echo "Host RDS:    $DB_HOST"
echo "Data Dir:    $DATA_DIR"


# Instalar dependencias si no existen
python3 -m pip install -q -r "$(dirname "$0")/requirements.txt" || true

# Ejecutar el script orquestador
python3 "$(dirname "$0")/ingest_to_s3.py"

echo "Validando objetos en Amazon S3:"
aws s3 ls "s3://$S3_BUCKET/raw/" --recursive --human-readable

