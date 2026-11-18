"""Read a Parquet schema and register an external Hive table on EMR."""

import re
import shlex
import time
import uuid
from urllib.parse import urlparse

import boto3
import pyarrow as pa
import pyarrow.parquet as pq

from config import Settings


def s3_location(uri: str) -> tuple[str, str]:
    parsed = urlparse(uri)

    if parsed.scheme != "s3" or not parsed.netloc or not parsed.path.strip("/"):
        raise ValueError("PARQUET_S3_URI must look like s3://bucket/folder/")
    if not uri.endswith("/"):
        raise ValueError("PARQUET_S3_URI must be a folder prefix ending in /")
    return parsed.netloc, parsed.path.lstrip("/")


def one_parquet_key(s3, bucket: str, prefix: str) -> str:
    keys = []

    for page in s3.get_paginator("list_objects_v2").paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if key.endswith(".parquet"):
                if "=" in key[len(prefix):]:
                    raise ValueError("Partitioned folders (key=value) need explicit Hive PARTITIONED BY")
                keys.append(key)
                if len(keys) == 1:
                    return keys[0]
    raise ValueError(f"No Parquet files found under s3://{bucket}/{prefix}")


def hive_type(dtype: pa.DataType) -> str:
    if pa.types.is_boolean(dtype):
        return "BOOLEAN"
    if pa.types.is_int8(dtype) or pa.types.is_int16(dtype):
        return "SMALLINT"
    if pa.types.is_int32(dtype) or pa.types.is_uint16(dtype):
        return "INT"
    if pa.types.is_int64(dtype) or pa.types.is_uint32(dtype):
        return "BIGINT"
    if pa.types.is_float32(dtype):
        return "FLOAT"
    if pa.types.is_float64(dtype):
        return "DOUBLE"
    if pa.types.is_string(dtype) or pa.types.is_large_string(dtype):
        return "STRING"
    if pa.types.is_binary(dtype) or pa.types.is_large_binary(dtype):
        return "BINARY"
    if pa.types.is_date(dtype):
        return "DATE"
    if pa.types.is_timestamp(dtype):
        return "TIMESTAMP"
    if pa.types.is_decimal(dtype):
        return f"DECIMAL({dtype.precision},{dtype.scale})"
    # Deliberately reject nested, unsigned-64, and ambiguous types.
    raise TypeError(f"Unsupported Parquet type for automatic Hive DDL: {dtype}")


def identifier(name: str) -> str:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
        raise ValueError(f"Unsupported SQL identifier: {name!r}")
    
    return f"`{name}`"


def build_ddl(settings: Settings, schema: pa.Schema) -> str:
    columns = ",\n  ".join(
        f"{identifier(field.name)} {hive_type(field.type)}" for field in schema
    )

    if not columns:
        raise ValueError("Empty Parquet schema")
    location = settings.parquet_s3_uri.rstrip("/") + "/"
    if "'" in location:
        raise ValueError("Single quotes in S3 path are unsupported")
    
    return (
        f"CREATE DATABASE IF NOT EXISTS {identifier(settings.hive_database)};\n"
        f"CREATE EXTERNAL TABLE IF NOT EXISTS "
        f"{identifier(settings.hive_database)}.{identifier(settings.hive_table)} (\n"
        f"  {columns}\n)\nSTORED AS PARQUET\nLOCATION '{location}';\n"
        f"DESCRIBE FORMATTED {identifier(settings.hive_database)}.{identifier(settings.hive_table)};\n"
        f"SELECT * FROM {identifier(settings.hive_database)}.{identifier(settings.hive_table)} LIMIT 5;\n"
    )


def catalog_with_hive(settings: Settings, cluster_id: str, timeout: int = 1800) -> None:
    bucket, prefix = s3_location(settings.parquet_s3_uri)
    s3 = boto3.client("s3", region_name=settings.region)
    sample_key = one_parquet_key(s3, bucket, prefix)

    # PyArrow reads Parquet metadata, not the full dataset.
    filesystem = pa.fs.S3FileSystem(region=settings.region)
    schema = pq.read_schema(f"{bucket}/{sample_key}", filesystem=filesystem)
    ddl = build_ddl(settings, schema)
    print(f"Hive DDL (inferred from s3://{bucket}/{sample_key}):\n{ddl}")

    # Upload a short-lived HiveQL script to the same S3 bucket.
    script_key = f"cataloging-temp/{uuid.uuid4().hex}.hql"
    script_uri = f"s3://{bucket}/{script_key}"
    s3.put_object(Bucket=bucket, Key=script_key, Body=ddl.encode("utf-8"))
    emr = boto3.client("emr", region_name=settings.region)
    try:
        # Fetch via AWS CLI on EMR, then invoke the local Hive CLI.
        command = (
            f"aws s3 cp {shlex.quote(script_uri)} /tmp/cataloging.hql && "
            "hive -f /tmp/cataloging.hql"
        )
        result = emr.add_job_flow_steps(
            JobFlowId=cluster_id,
            Steps=[{
                "Name": "Catalog Parquet in local Hive metastore",
                "ActionOnFailure": "CONTINUE",
                "HadoopJarStep": {"Jar": "command-runner.jar", "Args": ["bash", "-c", command]},
            }],
        )
        step_id = result["StepIds"][0]

        print(f"EMR Hive step: {step_id}")
        
        deadline = time.monotonic() + timeout
        
        while time.monotonic() < deadline:
            status = emr.describe_step(ClusterId=cluster_id, StepId=step_id)["Step"]["Status"]
            state = status["State"]
            print(f"Hive step: {state}")
            if state == "COMPLETED":
                print("Hive table created and verified. Check EMR step stdout for DESCRIBE/SELECT.")
                return
            if state in {"FAILED", "CANCELLED", "INTERRUPTED"}:
                raise RuntimeError(f"Hive step {state}: {status.get('FailureDetails', {})}")
            time.sleep(20)
            
        raise TimeoutError("Hive step timed out")
    finally:
        s3.delete_object(Bucket=bucket, Key=script_key)
