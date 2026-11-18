"""Lectura del Parquet de exoplanetas desde S3 (credenciales del entorno AWS) o desde una ruta local."""
import io
import os

import boto3
import pandas as pd

BUCKET = os.getenv("S3_BUCKET", "exoplanets-data-lake-225180590593-us-east-1")
PREFIX = os.getenv("S3_PREFIX", "trusted/exoplanets/")
# Si DATASET_PATH existe (archivo o carpeta .parquet) se lee local, útil para pruebas.
LOCAL_PATH = os.getenv("DATASET_PATH")


def load_exoplanets() -> pd.DataFrame:
    if LOCAL_PATH:
        return pd.read_parquet(LOCAL_PATH)

    s3 = boto3.client("s3")  # usa el rol IAM / credenciales del entorno
    frames = []
    for page in s3.get_paginator("list_objects_v2").paginate(Bucket=BUCKET, Prefix=PREFIX):
        for obj in page.get("Contents", []):
            if obj["Key"].endswith(".parquet"):
                body = s3.get_object(Bucket=BUCKET, Key=obj["Key"])["Body"].read()
                frames.append(pd.read_parquet(io.BytesIO(body)))
    if not frames:
        raise FileNotFoundError(f"No hay archivos Parquet en s3://{BUCKET}/{PREFIX}")
    return pd.concat(frames, ignore_index=True)
