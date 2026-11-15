#!/usr/bin/env python3
"""
Script: ingest_to_s3.py
Descripción: Pipeline automatizado de ingesta hacia la zona RAW del Data Lake
             en Amazon S3. Extrae y carga de forma centralizada las 3 fuentes:
             1. Amazon RDS MariaDB -> s3://<bucket>/raw/rds/
             2. Archivos en EC2    -> s3://<bucket>/raw/ec2_csv/
             3. NASA TAP API       -> s3://<bucket>/raw/nasa_api/

"""

import argparse
import csv
import io
import json
import logging
import os
import sys
import time
import boto3
from botocore.exceptions import ClientError
import pymysql
import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("DataLake_Ingestion")


def get_s3_client():
    """Inicializa el cliente de S3 mediante credenciales de IAM (LabRole o configuradas)."""
    return boto3.client("s3")


def verify_bucket_exists(s3_client, bucket_name: str):
    """Verifica la existencia y accesibilidad del bucket de S3."""
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        logger.info(f"Conexión exitosa con el bucket S3: s3://{bucket_name}/")
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code")
        logger.error(f"No se pudo acceder al bucket '{bucket_name}'. Código: {error_code}")
        raise


def ingest_rds_to_s3(s3_client, bucket_name: str, db_config: dict) -> dict:
    """Extrae las tablas de MariaDB y las carga directamente a la zona RAW en S3."""
   
    logger.info("[1/3] Iniciando ingesta desde Amazon RDS MariaDB...")

    connection = pymysql.connect(
        host=db_config["host"],
        user=db_config["user"],
        password=db_config["password"],
        database=db_config["database"],
        port=db_config["port"],
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor
    )

    results = {}
    tables = [
        {"name": "stars", "query": "SELECT star_id, hostname FROM stars ORDER BY star_id", "s3_key": "raw/rds/stars/stars.csv"},
        {"name": "planetary_systems", "query": "SELECT system_id, star_id, sy_dist, sy_pnum FROM planetary_systems ORDER BY system_id", "s3_key": "raw/rds/planetary_systems/planetary_systems.csv"}
    ]

    try:
        with connection.cursor() as cursor:
            for table in tables:
                cursor.execute(table["query"])
                rows = cursor.fetchall()
                total_rows = len(rows)

                if not rows:
                    logger.warning(f"La tabla '{table['name']}' no contiene registros.")
                    continue

                # Escribir registros en memoria en formato CSV
                csv_buffer = io.StringIO()
                writer = csv.DictWriter(csv_buffer, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)

                # Subir buffer a S3
                csv_bytes = csv_buffer.getvalue().encode("utf-8")
                s3_client.put_object(
                    Bucket=bucket_name,
                    Key=table["s3_key"],
                    Body=csv_bytes,
                    ContentType="text/csv"
                )

                size_kb = round(len(csv_bytes) / 1024, 2)
                logger.info(f"Tabla '{table['name']}': {total_rows:,} registros cargados -> s3://{bucket_name}/{table['s3_key']} ({size_kb} KB)")
                results[table["name"]] = {"rows": total_rows, "s3_uri": f"s3://{bucket_name}/{table['s3_key']}"}

    finally:
        connection.close()

    return results


def ingest_ec2_csv_to_s3(s3_client, bucket_name: str, data_dir: str) -> dict:
    """Sube el archivo CSV del catálogo almacenado en la EC2 hacia S3 Raw."""

    logger.info("[2/3] Iniciando ingesta desde Filesystem EC2 (CSV)...")

    csv_file = os.path.join(data_dir, "exoplanetas_catalogo.csv")
    s3_key = "raw/ec2_csv/exoplanetas_catalogo.csv"

    # Si el archivo no existe en el disco, descargarlo dinámicamente de NASA
    if not os.path.exists(csv_file):
        logger.warning(f"No se encontró '{csv_file}'. Descargando directamente desde NASA TAP...")
        os.makedirs(data_dir, exist_ok=True)
        tap_url = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"
        query = "SELECT pl_name, hostname, discoverymethod, disc_year, disc_facility FROM ps WHERE default_flag = 1 AND pl_name IS NOT NULL ORDER BY pl_name"
        r = requests.get(tap_url, params={"query": query, "format": "csv"}, timeout=120)
        r.raise_for_status()
        with open(csv_file, "w", encoding="utf-8") as f:
            f.write(r.text)

    # Subir a S3
    s3_client.upload_file(
        Filename=csv_file,
        Bucket=bucket_name,
        Key=s3_key,
        ExtraArgs={"ContentType": "text/csv"}
    )

    file_size_kb = round(os.path.getsize(csv_file) / 1024, 2)
    with open(csv_file, "r", encoding="utf-8") as f:
        line_count = sum(1 for _ in f) - 1

    logger.info(f"Catálogo CSV: {line_count:,} registros cargados -> s3://{bucket_name}/{s3_key} ({file_size_kb} KB)")
    return {"records": line_count, "s3_uri": f"s3://{bucket_name}/{s3_key}"}


def ingest_nasa_api_to_s3(s3_client, bucket_name: str, data_dir: str) -> dict:
    """Consume la API de NASA TAP (o lee el JSON existente) y lo ingesta en S3 Raw."""
    logger.info("[3/3] Iniciando ingesta desde NASA Exoplanet API (TAP)...")
   

    json_file = os.path.join(data_dir, "exoplanetas_parametros_api.json")
    s3_key = "raw/nasa_api/exoplanetas_parametros_api.json"

    # Si no existe en disco local, consultarlo directamente desde la API
    if not os.path.exists(json_file):
        logger.info("Consultando endpoint oficial TAP de NASA...")
        tap_url = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"
        query = "SELECT pl_name, pl_rade, pl_bmasse, pl_orbper FROM ps WHERE default_flag = 1 AND pl_name IS NOT NULL ORDER BY pl_name"
        r = requests.get(tap_url, params={"query": query, "format": "json"}, timeout=180)
        r.raise_for_status()
        json_content = r.text
        os.makedirs(data_dir, exist_ok=True)
        with open(json_file, "w", encoding="utf-8") as f:
            f.write(json_content)
    else:
        with open(json_file, "r", encoding="utf-8") as f:
            json_content = f.read()

    s3_client.upload_file(
        Filename=json_file,
        Bucket=bucket_name,
        Key=s3_key,
        ExtraArgs={"ContentType": "application/json"}
    )

    records = json.loads(json_content)
    total_records = len(records)
    file_size_kb = round(os.path.getsize(json_file) / 1024, 2)

    logger.info(f"Parámetros API: {total_records:,} registros cargados -> s3://{bucket_name}/{s3_key} ({file_size_kb} KB)")
    return {"records": total_records, "s3_uri": f"s3://{bucket_name}/{s3_key}"}


def main():
    parser = argparse.ArgumentParser(description="Pipeline de Ingesta Automatizada a AWS S3 (Zona Raw)")
    parser.add_argument("--bucket", default=os.environ.get("S3_BUCKET"), help="Nombre del bucket S3 de destino")
    parser.add_argument("--db-host", default=os.environ.get("DB_HOST"), help="Endpoint de RDS MariaDB")
    parser.add_argument("--db-user", default=os.environ.get("DB_USER", "admin_exoplanets"), help="Usuario de la BD")
    parser.add_argument("--db-password", default=os.environ.get("DB_PASSWORD"), help="Contraseña de la BD")
    parser.add_argument("--db-name", default=os.environ.get("DB_NAME", "exoplanets_db"), help="Nombre de la BD")
    parser.add_argument("--db-port", type=int, default=int(os.environ.get("DB_PORT", 3306)), help="Puerto de la BD")
    parser.add_argument("--data-dir", default=os.path.expanduser(os.environ.get("DATA_DIR", "~/data")), help="Directorio con archivos locales")

    args = parser.parse_args()

    if not args.bucket:
        logger.error("Debe especificar el bucket con --bucket o la variable de entorno S3_BUCKET.")
        sys.exit(1)

    if not args.db_host or not args.db_password:
        logger.error("Debe especificar DB_HOST y DB_PASSWORD mediante argumentos o variables de entorno.")
        sys.exit(1)

    s3 = get_s3_client()
    verify_bucket_exists(s3, args.bucket)

    db_config = {
        "host": args.db_host,
        "user": args.db_user,
        "password": args.db_password,
        "database": args.db_name,
        "port": args.db_port
    }

    start_time = time.time()
    logger.info(f"Iniciando Pipeline de Ingesta hacia: s3://{args.bucket}/raw/")

    rds_summary = ingest_rds_to_s3(s3, args.bucket, db_config)
    ec2_summary = ingest_ec2_csv_to_s3(s3, args.bucket, args.data_dir)
    api_summary = ingest_nasa_api_to_s3(s3, args.bucket, args.data_dir)

    total_time = round(time.time() - start_time, 2)

    print("\n" + "=" * 65)
    print("      RESUMEN DE INGESTA AUTOMATIZADA AL DATA LAKE (S3 RAW)")
    print("=" * 65)
    print(f"Bucket de destino:          s3://{args.bucket}/")
    print(f"Tiempo total de ejecución:  {total_time} segundos")
    print("-" * 65)
    print("Objetos cargados en la Zona RAW:")
    for tbl, info in rds_summary.items():
        print(f"  • [RDS {tbl}]:         {info['s3_uri']} ({info['rows']:,} filas)")
    print(f"  • [EC2 Catálogo CSV]:     {ec2_summary['s3_uri']} ({ec2_summary['records']:,} filas)")
    print(f"  • [NASA API JSON]:        {api_summary['s3_uri']} ({api_summary['records']:,} filas)")
    print("=" * 65)
    print("Comando para validar en AWS CLI:")
    print(f"aws s3 ls s3://{args.bucket}/raw/ --recursive --human-readable")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    main()
