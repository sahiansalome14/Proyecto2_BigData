#!/usr/bin/env python3
"""
Script: extract_api.py
Descripción: Consume la API pública Table Access Protocol (TAP) del
             NASA Exoplanet Archive para extraer los parámetros físicos
             y orbitales de los exoplanetas confirmados:
             - pl_name:  Nombre del exoplaneta (clave de enlace)
             - pl_rade:  Radio del planeta en radios terrestres
             - pl_bmasse: Masa del planeta en masas terrestres
             - pl_orbper: Periodo orbital en días
Uso:
    python extract_api.py [--format json|csv] [--output RUTA] [--limit N]
"""

import argparse
import json
import logging
import os
import sys
import time
import requests

# Configuración del registro de eventos (logging)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("NASA_TAP_Extractor")

TAP_SYNC_URL = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"


def build_adql_query(limit: int = None) -> str:
    """
    Construye la consulta ADQL para el servicio TAP de NASA.
    Solo selecciona registros confirmados (default_flag = 1) con nombre válido.
    """
    top_clause = f"TOP {limit} " if limit and limit > 0 else ""
    query = f"""
    SELECT {top_clause}pl_name, pl_rade, pl_bmasse, pl_orbper
    FROM ps
    WHERE default_flag = 1
      AND pl_name IS NOT NULL
    ORDER BY pl_name
    """.strip()
    return query


def extract_data(format_type: str = "json", limit: int = None, timeout: int = 180) -> str:
    """
    Envía la solicitud HTTP GET al servicio TAP y retorna el contenido en texto.
    """
    query = build_adql_query(limit)
    params = {
        "query": query,
        "format": format_type
    }

    logger.info("Iniciando consulta al NASA Exoplanet Archive TAP...")
    logger.info(f"URL: {TAP_SYNC_URL}")
    logger.info(f"Formato solicitado: {format_type}")
    logger.info(f"Consulta ADQL:\n{query}")

    start_time = time.time()
    try:
        response = requests.get(
            TAP_SYNC_URL,
            params=params,
            timeout=timeout,
            headers={"User-Agent": "BigDataExoplanetsProject/1.0"}
        )
        response.raise_for_status()
    except requests.exceptions.Timeout:
        logger.error(f"Tiempo de espera agotado ({timeout}s) al consultar la API de NASA.")
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"Error en la petición HTTP: {e}")
        raise

    elapsed = round(time.time() - start_time, 2)
    logger.info(f"Respuesta recibida exitosamente en {elapsed} segundos (Status: {response.status_code}).")
    return response.text


def analyze_and_save_data(raw_text: str, format_type: str, output_path: str):
    """
    Analiza las métricas del conjunto obtenido y guarda el archivo en disco.
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(raw_text)

    file_size_kb = round(os.path.getsize(output_path) / 1024, 2)
    logger.info(f"Archivo guardado exitosamente en: {output_path} ({file_size_kb} KB)")

    # Métricas y resumen descriptivo
    if format_type == "json":
        try:
            records = json.loads(raw_text)
            total = len(records)
            has_rade = sum(1 for r in records if r.get("pl_rade") is not None)
            has_mass = sum(1 for r in records if r.get("pl_bmasse") is not None)
            has_orbper = sum(1 for r in records if r.get("pl_orbper") is not None)

            print("\n" + "=" * 60)
            print("         RESUMEN DE EXTRACCIÓN - API NASA TAP")
            print("=" * 60)
            print(f"Total de exoplanetas extraídos:      {total:,}")
            print(f"Planetas con Radio (pl_rade):       {has_rade:,} ({has_rade/total*100:.1f}%)")
            print(f"Planetas con Masa (pl_bmasse):      {has_mass:,} ({has_mass/total*100:.1f}%)")
            print(f"Planetas con Periodo (pl_orbper):   {has_orbper:,} ({has_orbper/total*100:.1f}%)")
            print("=" * 60)
            print("\nMuestra de los primeros 3 registros:")
            print(json.dumps(records[:3], indent=2))
            print("=" * 60 + "\n")
        except json.JSONDecodeError:
            logger.warning("No se pudo parsear el resultado como JSON para métricas.")
    else:
        lines = raw_text.strip().split("\n")
        print("\n" + "=" * 60)
        print("         RESUMEN DE EXTRACCIÓN - API NASA TAP (CSV)")
        print("=" * 60)
        print(f"Total de líneas (con cabecera):     {len(lines):,}")
        print("Primeras 3 líneas:")
        for line in lines[:4]:
            print("  ", line)
        print("=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Extractor de parámetros de exoplanetas desde NASA TAP API")
    parser.add_argument(
        "--format",
        choices=["json", "csv"],
        default="json",
        help="Formato de salida de los datos (por defecto: json)"
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Ruta del archivo de salida (por defecto: ./exoplanetas_parametros_api.<format>)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Límite opcional de registros a extraer (ej. 10 para pruebas)"
    )

    args = parser.parse_args()

    default_output = f"exoplanetas_parametros_api.{args.format}"
    output_path = args.output if args.output else os.path.join(os.path.dirname(__file__), default_output)

    try:
        content = extract_data(format_type=args.format, limit=args.limit)
        analyze_and_save_data(content, args.format, output_path)
    except Exception as e:
        logger.error(f"Fallo durante la extracción: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
