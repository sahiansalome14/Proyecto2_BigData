"""Orchestrate independent Glue and Hive cataloging exercises."""

import argparse

from config import Settings
from emr_cluster import create_cluster, terminate_cluster, wait_for_cluster
from glue_catalog import catalog_with_glue
from hive_catalog import catalog_with_hive


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--create-cluster", action="store_true", help="Launch a billable EMR cluster")
    parser.add_argument("--cluster-id", help="Reuse an existing EMR cluster")
    parser.add_argument("--terminate-after", action="store_true", help="Terminate EMR after the run")
    
    args = parser.parse_args()
    
    if args.create_cluster == bool(args.cluster_id):
        parser.error("Specify exactly one of --create-cluster or --cluster-id")
    if args.terminate_after and not args.create_cluster:
        parser.error("--terminate-after only works for a cluster created by this run")

    settings = Settings.from_env()

    print("Cataloging with Glue...")
    
    catalog_with_glue(settings)

    cluster_id = None
    created = False
    try:
        if args.create_cluster:
            cluster_id = create_cluster(settings)
            created = True
        else:
            cluster_id = args.cluster_id
            
        wait_for_cluster(cluster_id, settings.region)

        print("Cataloging with Hive...")
        catalog_with_hive(settings, cluster_id)
    finally:
        if created and args.terminate_after and cluster_id:
            terminate_cluster(cluster_id, settings.region)

        elif created and cluster_id:
            print(f"IMPORTANT: EMR {cluster_id} is still running and accruing charges")

if __name__ == "__main__":
    main()
