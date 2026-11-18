"""Configuration shared by cataloging modules."""

import os
from dataclasses import dataclass

def required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"Set the {name} environment variable")
    return value


@dataclass(frozen=True)
class Settings:
    region: str
    parquet_s3_uri: str
    glue_database: str
    glue_crawler: str
    glue_role_arn: str
    hive_database: str
    hive_table: str
    emr_release: str
    emr_subnet_id: str
    emr_service_role: str
    emr_ec2_role: str
    emr_instance_type: str
    emr_log_uri: str | None

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            region=os.getenv("AWS_REGION", "us-east-1"),
            parquet_s3_uri=required("PARQUET_S3_URI"),
            glue_database=os.getenv("GLUE_DATABASE", "curated_glue"),
            glue_crawler=os.getenv("GLUE_CRAWLER", "curated-parquet-crawler"),
            glue_role_arn=required("GLUE_ROLE_ARN"),
            hive_database=os.getenv("HIVE_DATABASE", "curated_hive"),
            hive_table=os.getenv("HIVE_TABLE", "curated_data"),
            emr_release=os.getenv("EMR_RELEASE", "emr-7.12.0"),
            emr_subnet_id=required("EMR_SUBNET_ID"),
            emr_service_role=os.getenv("EMR_SERVICE_ROLE", "EMR_DefaultRole"),
            emr_ec2_role=os.getenv("EMR_EC2_ROLE", "EMR_EC2_DefaultRole"),
            emr_instance_type=os.getenv("EMR_INSTANCE_TYPE", "m4.xlarge"),
            emr_log_uri=os.getenv("EMR_LOG_URI") or None,
        )
