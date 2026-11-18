"""Lambda única detrás de API Gateway (HTTP API). Lee el Parquet de S3 con Boto3 + PyArrow.

Endpoints:
  GET /planets?q=&size_category=&earth_like=true   (filtros combinables)
  GET /statistics/size
"""
import io
import json
import os

import boto3
import pyarrow.parquet as pq

BUCKET = os.getenv("S3_BUCKET", "exoplanets-data-lake-225180590593-us-east-1")
PREFIX = os.getenv("S3_PREFIX", "trusted/exoplanets/")
LOCAL_PARQUET = os.getenv("LOCAL_PARQUET")  # solo para pruebas locales
MAX_RESULTS = 200
COLUMNS = ["pl_name", "hostname", "pl_rade", "pl_bmasse", "pl_orbper", "sy_dist",
           "discoverymethod", "disc_year", "size_category", "is_earth_similar"]

_cache = None  # se reutiliza mientras la Lambda esté "caliente"


def load_planets():
    global _cache
    if _cache is None:
        if LOCAL_PARQUET:
            _cache = pq.read_table(LOCAL_PARQUET, columns=COLUMNS).to_pylist()
        else:
            s3 = boto3.client("s3")  # usa el rol IAM de la Lambda
            _cache = []
            for page in s3.get_paginator("list_objects_v2").paginate(Bucket=BUCKET, Prefix=PREFIX):
                for obj in page.get("Contents", []):
                    if obj["Key"].endswith(".parquet"):
                        body = s3.get_object(Bucket=BUCKET, Key=obj["Key"])["Body"].read()
                        _cache += pq.read_table(io.BytesIO(body), columns=COLUMNS).to_pylist()
    return _cache


def response(status, body):
    return {"statusCode": status, "headers": {"Content-Type": "application/json"},
            "body": json.dumps(body, ensure_ascii=False)}


def get_planets(params):
    q = (params.get("q") or "").strip()
    size = (params.get("size_category") or "").strip()
    earth = (params.get("earth_like") or "").lower()
    if earth not in ("", "true", "false"):
        return response(400, {"error": "earth_like debe ser true o false"})
    if len(q) > 100 or len(size) > 100:
        return response(400, {"error": "parámetro demasiado largo"})

    rows = load_planets()
    if q:
        rows = [r for r in rows if r["pl_name"] and q.lower() in r["pl_name"].lower()]
    if size:
        rows = [r for r in rows if r["size_category"] == size]
    if earth == "true":
        rows = [r for r in rows if r["is_earth_similar"]]
    return response(200, {"total": len(rows), "limit": MAX_RESULTS, "planets": rows[:MAX_RESULTS]})


def get_size_statistics():
    counts = {}
    for r in load_planets():
        cat = r["size_category"] or "Sin categoría"
        counts[cat] = counts.get(cat, 0) + 1
    return response(200, {"statistics": [{"size_category": k, "count": v} for k, v in counts.items()]})


def lambda_handler(event, context):
    path = event.get("rawPath") or event.get("path", "")
    method = (event.get("requestContext", {}).get("http", {}).get("method")
              or event.get("httpMethod", "GET"))
    if method != "GET":
        return response(405, {"error": "método no permitido"})
    try:
        if path.rstrip("/").endswith("/planets"):
            return get_planets(event.get("queryStringParameters") or {})
        if path.rstrip("/").endswith("/statistics/size"):
            return get_size_statistics()
        return response(404, {"error": "ruta no encontrada"})
    except Exception as e:  # error inesperado: no exponer detalles internos
        print("ERROR:", e)
        return response(500, {"error": "error interno"})
