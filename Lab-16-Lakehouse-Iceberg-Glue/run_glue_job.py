"""
run_glue_job.py
Uploads the PySpark script to S3, registers or updates the AWS Glue ETL Job
configured for Apache Iceberg, triggers execution, and monitors the run until completion.
"""

import json
import time
import boto3

def load_config():
    with open("lakehouse_config.json", "r") as f:
        return json.load(f)

def run():
    config = load_config()
    bucket = config["bucket_name"]
    region = config["region"]
    glue_db = config["glue_db_name"]
    role_arn = config["glue_role_arn"]

    s3 = boto3.client("s3", region_name=region)
    glue = boto3.client("glue", region_name=region)

    job_name = "iceberg-bronze-to-silver-etl"
    script_local_path = "glue_bronze_to_silver.py"
    script_s3_key = "scripts/glue_bronze_to_silver.py"
    script_s3_uri = f"s3://{bucket}/{script_s3_key}"

    # 1. Upload PySpark ETL script to S3
    print(f"[1/3] Uploading ETL script to {script_s3_uri} ...")
    s3.upload_file(script_local_path, bucket, script_s3_key)

    # 2. Register or update the Glue Job with native Iceberg configurations
    print(f"[2/3] Configuring Glue Job '{job_name}' ...")
    spark_conf = (
        "spark.sql.catalog.glue_catalog=org.apache.iceberg.spark.SparkCatalog "
        f"--conf spark.sql.catalog.glue_catalog.warehouse=s3://{bucket}/silver/ "
        "--conf spark.sql.catalog.glue_catalog.catalog-impl=org.apache.iceberg.aws.glue.GlueCatalog "
        "--conf spark.sql.catalog.glue_catalog.io-impl=org.apache.iceberg.aws.s3.S3FileIO "
        "--conf spark.sql.extensions=org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions"
    )

    job_args = {
        "--job-language": "python",
        "--datalake-formats": "iceberg",
        "--enable-continuous-cloudwatch-log": "true",
        "--BUCKET_NAME": bucket,
        "--GLUE_DB": glue_db,
        "--conf": spark_conf
    }

    job_definition = {
        "Name": job_name,
        "Role": role_arn,
        "Command": {
            "Name": "glueetl",
            "ScriptLocation": script_s3_uri,
            "PythonVersion": "3"
        },
        "DefaultArguments": job_args,
        "GlueVersion": "4.0",
        "WorkerType": "G.1X",
        "NumberOfWorkers": 2,
        "Timeout": 15
    }

    try:
        glue.create_job(**job_definition)
        print(f"  Created Glue job: {job_name}")
    except glue.exceptions.AlreadyExistsException:
        update_def = job_definition.copy()
        update_def["JobName"] = update_def.pop("Name")
        update_def["JobUpdate"] = {
            "Role": update_def.pop("Role"),
            "Command": update_def.pop("Command"),
            "DefaultArguments": update_def.pop("DefaultArguments"),
            "GlueVersion": update_def.pop("GlueVersion"),
            "WorkerType": update_def.pop("WorkerType"),
            "NumberOfWorkers": update_def.pop("NumberOfWorkers"),
            "Timeout": update_def.pop("Timeout")
        }
        glue.update_job(**update_def)
        print(f"  Updated existing Glue job: {job_name}")

    # 3. Trigger Job Run & Poll Status
    print(f"\n[3/3] Starting Glue Job run for '{job_name}' ...")
    response = glue.start_job_run(JobName=job_name)
    run_id = response["JobRunId"]
    print(f"  Job Run ID: {run_id}")
    print("  Provisioning Spark workers and running Iceberg ETL (typically 2-3 minutes) ...")

    while True:
        status_res = glue.get_job_run(JobName=job_name, RunId=run_id)
        state = status_res["JobRun"]["JobRunState"]
        print(f"  Current Status: {state}")

        if state in ["SUCCEEDED"]:
            print(f"\nGlue Job {job_name} finished successfully.")
            break
        elif state in ["FAILED", "STOPPED", "TIMEOUT"]:
            error_message = status_res["JobRun"].get("ErrorMessage", "Unknown error")
            print(f"\nJob failed with status {state}: {error_message}")
            break

        time.sleep(20)

if __name__ == "__main__":
    run()