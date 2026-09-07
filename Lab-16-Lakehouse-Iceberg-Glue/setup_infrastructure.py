"""
setup_infrastructure.py
Provisions S3 storage, Glue Data Catalog database, IAM role,
and Athena Engine v3 workgroup for the Iceberg Medallion Lakehouse.
"""

import json
import boto3

def setup():
    session = boto3.Session()
    region = session.region_name or "us-east-1"
    sts = session.client("sts")
    account_id = sts.get_caller_identity()["Account"]
    
    bucket_name = f"weather-lakehouse-iceberg-{account_id}-{region}"
    glue_db_name = "weather_lakehouse_db"
    workgroup_name = "iceberg-lakehouse-wg"
    glue_role_name = "AWSGlueIcebergLakehouseRole"

    print(f"Target AWS Region: {region}")
    print(f"Target AWS Account: {account_id}")

    # 1. Provision S3 Bucket
    s3 = session.client("s3")
    print(f"\n[1/4] Ensuring S3 Bucket exists: s3://{bucket_name} ...")
    try:
        if region == "us-east-1":
            s3.create_bucket(Bucket=bucket_name)
        else:
            s3.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={"LocationConstraint": region}
            )
        print(f"  Created bucket: s3://{bucket_name}")
    except s3.exceptions.BucketAlreadyOwnedByYou:
        print(f"  Bucket s3://{bucket_name} already exists and is owned by you.")

    # 2. Create Glue Catalog Database
    glue = session.client("glue")
    print(f"\n[2/4] Creating Glue Database: {glue_db_name} ...")
    try:
        glue.create_database(
            DatabaseInput={
                "Name": glue_db_name,
                "Description": "Database for DEA Lab 16 Apache Iceberg Medallion Lakehouse",
                "LocationUri": f"s3://{bucket_name}/silver/"
            }
        )
        print(f"  Created Glue database: {glue_db_name}")
    except glue.exceptions.AlreadyExistsException:
        print(f"  Glue database {glue_db_name} already exists.")

    # 3. Create Athena Engine v3 Workgroup
    athena = session.client("athena")
    print(f"\n[3/4] Configuring Athena Workgroup: {workgroup_name} ...")
    athena_output_path = f"s3://{bucket_name}/athena-results/"
    try:
        athena.create_work_group(
            Name=workgroup_name,
            Configuration={
                "ResultConfiguration": {"OutputLocation": athena_output_path},
                "EnforceWorkGroupConfiguration": True,
                "PublishCloudWatchMetricsEnabled": True,
                "EngineVersion": {
                    "SelectedEngineVersion": "Athena engine version 3"
                }
            },
            Description="Workgroup for querying Apache Iceberg tables on Athena v3"
        )
        print(f"  Created Athena workgroup '{workgroup_name}' pinned to Engine v3.")
    except athena.exceptions.InvalidRequestException as e:
        if "already exists" in str(e):
            print(f"  Workgroup {workgroup_name} already exists.")
        else:
            raise

    # 4. Create IAM Role for AWS Glue
    iam = session.client("iam")
    print(f"\n[4/4] Configuring IAM Execution Role: {glue_role_name} ...")
    assume_role_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Service": "glue.amazonaws.com"},
                "Action": "sts:AssumeRole"
            }
        ]
    }
    
    try:
        iam.create_role(
            RoleName=glue_role_name,
            AssumeRolePolicyDocument=json.dumps(assume_role_policy),
            Description="Execution role for AWS Glue PySpark Iceberg ETL"
        )
        print(f"  Created IAM role: {glue_role_name}")
    except iam.exceptions.EntityAlreadyExistsException:
        print(f"  IAM role {glue_role_name} already exists.")

    # Attach required AWS managed policies
    managed_policies = [
        "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole",
        "arn:aws:iam::aws:policy/AmazonS3FullAccess"
    ]
    for policy in managed_policies:
        iam.attach_role_policy(RoleName=glue_role_name, PolicyArn=policy)
    
    print("\nInfrastructure Provisioning Complete.")
    print(f"Bucket: s3://{bucket_name}")
    print(f"Glue DB: {glue_db_name}")
    print(f"Athena Workgroup: {workgroup_name}")
    print(f"IAM Role: {glue_role_name}")

    # Save details locally for subsequent scripts
    config = {
        "bucket_name": bucket_name,
        "region": region,
        "glue_db_name": glue_db_name,
        "workgroup_name": workgroup_name,
        "glue_role_arn": f"arn:aws:iam::{account_id}:role/{glue_role_name}"
    }
    with open("lakehouse_config.json", "w") as f:
        json.dump(config, f, indent=2)
    print("Configuration exported to 'lakehouse_config.json'.")

if __name__ == "__main__":
    setup()