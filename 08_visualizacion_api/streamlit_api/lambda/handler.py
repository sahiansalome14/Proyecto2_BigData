"""Lambda  detrás de API Gateway (HTTP API). Lee el Parquet de S3 con Boto3 + PyArrow.

Endpoints:
  GET /planets?q=&size_category=&earth_like=true&sort=sy_dist   (filtros combinables; sort opcional)
  GET /statistics/size
"""
import io
import json
import os
import boto3
import pyarrow.parquet as pq

BUCKET = os.getenv("S3_BUCKET", "exoplanets-data-lake-225180590593-us-east-1")
PREFIX = os.getenv("S3_PREFIX", "trusted/exoplanets/") #carpeta dentro del bucket donde estan los datos
MAX_RESULTS = 200 #por consulta
COLUMNS = ["pl_name", "hostname", "pl_rade", "pl_bmasse", "pl_orbper", "sy_dist",
           "discoverymethod", "disc_year", "size_category", "is_earth_similar"]

_cache = None  


def read_from_s3():
    """Lee todos los .parquet bajo PREFIX y devuelve una lista de diccionarios."""
    s3 = boto3.client("s3")  # crea el cliente de s3
    rows = []  #lista donde se acumularan los planetas
    for page in s3.get_paginator("list_objects_v2").paginate(Bucket=BUCKET, Prefix=PREFIX): #recorre los archivos .parquet de la carpeta
        for obj in page.get("Contents", []):
            if obj["Key"].endswith(".parquet"):
                body = s3.get_object(Bucket=BUCKET, Key=obj["Key"])["Body"].read()
                rows += pq.read_table(io.BytesIO(body), columns=COLUMNS).to_pylist() #lee todos los bytes del .parquet y la convierte en una lsita de diccionarios uno por planeta
    return rows


def load_planets(): #lee de s3 y lo guarda en cache
    global _cache
    if _cache is None:
        _cache = read_from_s3()
    return _cache


def response(status, body): #arma la respuesta en json el formaro que API GATEWAY se exige
    return {"statusCode": status, "headers": {"Content-Type": "application/json"},
            "body": json.dumps(body, ensure_ascii=False)}

# ENDPOINT GET /planets
def get_planets(params):
    """Lista planetas aplicando los filtros recibidos (todos opcionales)."""
    q = (params.get("q") or "").strip().lower()
    size = (params.get("size_category") or "").strip()
    earth = (params.get("earth_like") or "").lower()
    sort = (params.get("sort") or "").strip()

    # 1. Validar parámetros
    if earth not in ("", "true", "false"):
        return response(400, {"error": "earth_like debe ser true o false"})
    if len(q) > 100 or len(size) > 100:
        return response(400, {"error": "parámetro demasiado largo"})
    if sort not in ("", "sy_dist"):
        return response(400, {"error": "sort solo admite sy_dist"})

    # 2. Filtrar -> returna cuantos coinciden
    rows = load_planets() #carga los planetas de cache o de s3
    if q: # si hay texto de busqueda, deja lso plantes que contenga esa busqueda
        rows = [r for r in rows if r["pl_name"] and q in r["pl_name"].lower()]
    if size: # si hay categoria deja solo esa
        rows = [r for r in rows if r["size_category"] == size]
    if earth == "true":  #si pide similar_a_tiera deja los que si
        rows = [r for r in rows if r["is_earth_similar"]]
    if sort:  # si se debe ordener lo hace asc
        rows = sorted((r for r in rows if r[sort] is not None), key=lambda r: r[sort])
    return response(200, {"total": len(rows), "limit": MAX_RESULTS, "sort": sort, "planets": rows[:MAX_RESULTS]})

# ENDPOINT  GET /statistics/size
def get_size_statistics():
    """Cuenta cuántos planetas hay por categoría de tamaño y devuelve una lista con (Cateogria y cantidad)"""
    counts = {}
    for r in load_planets():
        cat = r["size_category"] or "Sin categoría"
        counts[cat] = counts.get(cat, 0) + 1
    return response(200, {"statistics": [{"size_category": k, "count": v} for k, v in counts.items()]})

# AWS lo llama cada vez que llega una peticion LLAMA A LOS 2 ENDPOINTS
def lambda_handler(event, context):
    path = (event.get("rawPath") or event.get("path", "")).rstrip("/") #obtiene la ruta pedida por ejemplo /planets
    method = (event.get("requestContext", {}).get("http", {}).get("method") #obtiene el metodo
              or event.get("httpMethod", "GET"))
    if method != "GET":
        return response(405, {"error": "método no permitido"})
    try:
        if path.endswith("/planets"): #como si o si es get 
            return get_planets(event.get("queryStringParameters") or {})
        if path.endswith("/statistics/size"):
            return get_size_statistics()
        return response(404, {"error": "ruta no encontrada"})
    except Exception as e:  # error inesperado: no exponer detalles internos
        print("ERROR:", e)
        return response(500, {"error": "error interno"})
