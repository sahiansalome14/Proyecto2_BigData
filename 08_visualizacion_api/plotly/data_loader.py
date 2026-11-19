"""Lectura del Parquet de exoplanetas desde S3 (credenciales del entorno AWS) o desde una ruta local."""
import io
import os

import boto3
import pandas as pd

BUCKET = os.getenv("S3_BUCKET", "exoplanets-data-lake-225180590593-us-east-1")
PREFIX = os.getenv("S3_PREFIX", "trusted/exoplanets/") #carpeta dentro del buckets
# Si DATASET_PATH existe (archivo o carpeta .parquet) se lee local, útil para pruebas.
LOCAL_PATH = os.getenv("DATASET_PATH")


def load_exoplanets() -> pd.DataFrame:
    if LOCAL_PATH:
        return pd.read_parquet(LOCAL_PATH)

    s3 = boto3.client("s3")  # crea la conexion con s3 y usa las credenciales de LabRole para leer en el 
    frames = []  #lista donde guarda los datos  ya leidos de cada archivo 
    for page in s3.get_paginator("list_objects_v2").paginate(Bucket=BUCKET, Prefix=PREFIX): #lista los archivos de la carpeta
        for obj in page.get("Contents", []):
            if obj["Key"].endswith(".parquet"): #solo toma los archivos .parquet
                body = s3.get_object(Bucket=BUCKET, Key=obj["Key"])["Body"].read() #descarga el archivo completo y lo deja en memoria
                frames.append(pd.read_parquet(io.BytesIO(body)))
    if not frames:
        raise FileNotFoundError(f"No hay archivos Parquet en s3://{BUCKET}/{PREFIX}")
    return pd.concat(frames, ignore_index=True)
