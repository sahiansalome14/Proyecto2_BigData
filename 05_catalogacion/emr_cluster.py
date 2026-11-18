"""Create, monitor and terminate an EMR-on-EC2 cluster running Hive."""

import time

import boto3

from config import Settings


def create_cluster(settings: Settings) -> str:
    emr = boto3.client("emr", region_name=settings.region)
    options = {
        "Name": "cataloging-hive-practice",
        "ReleaseLabel": settings.emr_release,
        "Applications": [{"Name": "Hive"}],
        "ServiceRole": settings.emr_service_role,
        "JobFlowRole": settings.emr_ec2_role,
        "Instances": {
            "Ec2SubnetId": settings.emr_subnet_id,
            "InstanceGroups": [{
                "Name": "Primary",
                "InstanceRole": "MASTER",
                "InstanceType": settings.emr_instance_type,
                "InstanceCount": 1,
                "Market": "ON_DEMAND",
            }],
            "KeepJobFlowAliveWhenNoSteps": True,
            "TerminationProtected": False,
        },
        "VisibleToAllUsers": True,
        "AutoTerminationPolicy": {"IdleTimeout": 3600},
    }
    if settings.emr_log_uri:
        options["LogUri"] = settings.emr_log_uri
    cluster_id = emr.run_job_flow(**options)["JobFlowId"]
    print(f"Created EMR cluster: {cluster_id} (billable until terminated)")
    return cluster_id


def wait_for_cluster(cluster_id: str, region: str, timeout: int = 2400) -> None:
    emr = boto3.client("emr", region_name=region)
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        state = emr.describe_cluster(ClusterId=cluster_id)["Cluster"]["Status"]["State"]
        print(f"EMR {cluster_id}: {state}")
        if state in {"WAITING", "RUNNING"}:
            return
        if state in {"TERMINATED", "TERMINATED_WITH_ERRORS", "TERMINATING"}:
            raise RuntimeError(f"EMR cluster failed: {state}")
        time.sleep(30)
    raise TimeoutError(f"EMR cluster did not become ready within {timeout}s")


def terminate_cluster(cluster_id: str, region: str) -> None:
    boto3.client("emr", region_name=region).terminate_job_flows(JobFlowIds=[cluster_id])
    print(f"Requested termination of EMR cluster {cluster_id}")
