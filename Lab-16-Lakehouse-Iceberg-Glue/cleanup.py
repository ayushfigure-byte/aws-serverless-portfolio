"""
cleanup.py
Tears down all Lab 16 lakehouse resources:
- Empties and deletes the S3 bucket (including versions)
- Deletes the Glue database and all Iceberg tables
- Deletes the AWS Glue ETL job
- Deletes the Athena Engine v3 workgroup
"""

import json
import boto3

def load_config():
    with open("lakehouse_config.json", "r") as f:
        return json.load(f)

def cleanup():
    config = load_config()
    bucket_name = config["bucket_name"]
    region = config["region"]
    glue_db = config["glue_db_name"]
    workgroup = config["workgroup_name"]
    job_name = "iceberg-bronze-to-silver-etl"

    s3 = boto3.resource("s3", region_name=region)
    glue = boto3.client("glue", region_name=region)
    athena = boto3.client("athena", region_name=region)

    print(f"Beginning teardown of Lab 16 resources in {region}...")

    # 1. Delete Athena Workgroup
    print(f"\n[1/4] Dropping Athena Workgroup: {workgroup} ...")
    try:
        athena.delete_work_group(WorkGroup=workgroup, RecursiveDeleteOption=True)
        print("  Athena workgroup deleted.")
    except Exception as e:
        print(f"  Athena cleanup notice: {e}")

    # 2. Delete Glue Job
    print(f"\n[2/4] Deleting AWS Glue Job: {job_name} ...")
    try:
        glue.delete_job(JobName=job_name)
        print("  Glue job deleted.")
    except Exception as e:
        print(f"  Glue job cleanup notice: {e}")

    # 3. Delete Glue Database and Tables
    print(f"\n[3/4] Dropping Glue Database: {glue_db} ...")
    try:
        glue.delete_database(Name=glue_db)
        print("  Glue database and associated catalog tables deleted.")
    except Exception as e:
        print(f"  Glue DB cleanup notice: {e}")

    # 4. Empty and Delete S3 Bucket
    print(f"\n[4/4] Emptying and deleting S3 Bucket: {bucket_name} ...")
    try:
        bucket = s3.Bucket(bucket_name)
        bucket.object_versions.delete()
        bucket.delete()
        print(f"  Bucket s3://{bucket_name} completely removed.")
    except Exception as e:
        print(f"  S3 cleanup notice: {e}")

    print("\nTeardown complete. All billable resources removed.")

if __name__ == "__main__":
    cleanup()