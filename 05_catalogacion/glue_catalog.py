"""Catalog existing S3 Parquet data with a Glue crawler."""

import time
import boto3

from config import Settings


def catalog_with_glue(settings: Settings, timeout: int = 1800) -> None:
    glue = boto3.client("glue", region_name=settings.region)

    try:
        glue.get_database(Name=settings.glue_database)

    except glue.exceptions.EntityNotFoundException:
        glue.create_database(DatabaseInput={"Name": settings.glue_database})

    target = {"S3Targets": [{"Path": settings.parquet_s3_uri}]}

    try:
        existing = glue.get_crawler(Name=settings.glue_crawler)["Crawler"]
        if (existing.get("DatabaseName") != settings.glue_database
                or existing.get("Targets", {}).get("S3Targets") != target["S3Targets"]):
            raise ValueError("Existing crawler has different database or S3 target; rename it")
        
    except glue.exceptions.EntityNotFoundException:
        glue.create_crawler(
            Name=settings.glue_crawler,
            Role=settings.glue_role_arn,
            DatabaseName=settings.glue_database,
            Targets=target,
        )

    # Wait until a previous run (if any) finishes.
    deadline = time.monotonic() + timeout
    while glue.get_crawler(Name=settings.glue_crawler)["Crawler"]["State"] != "READY":
        if time.monotonic() > deadline:
            raise TimeoutError("Crawler not ready")
        time.sleep(10)

    previous_start = glue.get_crawler(Name=settings.glue_crawler)["Crawler"].get("LastCrawl", {}).get("StartTime")
    
    # Execute crawler
    glue.start_crawler(Name=settings.glue_crawler) 

    while time.monotonic() < deadline:
        crawler = glue.get_crawler(Name=settings.glue_crawler)["Crawler"]
        last = crawler.get("LastCrawl", {})
        start = last.get("StartTime")

        if (crawler["State"] == "READY" and start and start != previous_start):
            if last.get("Status") != "SUCCEEDED":
                raise RuntimeError(f"Crawler failed: {last}")
            break
        time.sleep(10)

    else:
        raise TimeoutError("Glue crawler exceeded timeout")

    print(f"Glue catalog tables in {settings.glue_database}:")
    
    paginator = glue.get_paginator("get_tables")

    for page in paginator.paginate(DatabaseName=settings.glue_database):
        for table in page["TableList"]:
            print(f"  {table['Name']}")
            for col in table.get("StorageDescriptor", {}).get("Columns", []):
                print(f"    {col['Name']}: {col['Type']}")
