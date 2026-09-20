import boto3
import json

# 1. Discover AWS identity
sts_client = boto3.client("sts")
account_id = sts_client.get_caller_identity()["Account"]
session = boto3.session.Session()
region = session.region_name or "us-east-1"

s3_client = boto3.client("s3", region_name=region)
iam_client = boto3.client("iam")

bucket_name = f"sagemaker-featurestore-{account_id}-{region}"

# 2. Create S3 Bucket for the Offline Feature Store
print(f"Checking S3 bucket: {bucket_name}...")
try:
    if region == "us-east-1":
        s3_client.create_bucket(Bucket=bucket_name)
    else:
        s3_client.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration={"LocationConstraint": region}
        )
    print(f"✓ Created S3 Offline Store bucket: {bucket_name}")
except s3_client.exceptions.BucketAlreadyOwnedByYou:
    print(f"✓ Bucket already exists and is owned by you: {bucket_name}")

# 3. Locate or verify SageMaker Execution Role
role_name = "NOAASageMakerExecutionRole"
try:
    role_arn = iam_client.get_role(RoleName=role_name)["Role"]["Arn"]
    print(f"✓ Found execution role: {role_arn}")
except iam_client.exceptions.NoSuchEntityException:
    # Fallback to general lab execution role if present
    role_arn = f"arn:aws:iam::{account_id}:role/service-role/AmazonSageMaker-ExecutionRole"
    print(f"! Using fallback role ARN: {role_arn}")

# 4. Save environment config locally
config = {
    "account_id": account_id,
    "region": region,
    "offline_store_bucket": bucket_name,
    "role_arn": role_arn,
    "feature_group_name": "customer-churn-features"
}

with open("feature_store_config.json", "w") as f:
    json.dump(config, f, indent=2)

print("\nInfrastructure configuration saved to feature_store_config.json:")
print(json.dumps(config, indent=2))
