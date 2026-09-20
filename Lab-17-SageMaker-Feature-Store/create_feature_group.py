import boto3
import json
import time

with open("feature_store_config.json") as f:
    config = json.load(f)

sagemaker_client = boto3.client("sagemaker", region_name=config["region"])

feature_group_name = config["feature_group_name"]
record_id_name = "customer_id"
event_time_name = "event_time"

# Clean schema strictly using FeatureName and FeatureType
feature_definitions = [
    {"FeatureName": "customer_id", "FeatureType": "String"},
    {"FeatureName": "event_time", "FeatureType": "Fractional"},
    {"FeatureName": "account_length", "FeatureType": "Integral"},
    {"FeatureName": "intl_plan", "FeatureType": "Integral"},
    {"FeatureName": "voice_mail_plan", "FeatureType": "Integral"},
    {"FeatureName": "total_day_minutes", "FeatureType": "Fractional"},
    {"FeatureName": "total_day_calls", "FeatureType": "Integral"},
    {"FeatureName": "customer_service_calls", "FeatureType": "Integral"},
    {"FeatureName": "churn", "FeatureType": "Integral"}
]

s3_uri = f"s3://{config['offline_store_bucket']}/offline-store/"

try:
    sagemaker_client.describe_feature_group(FeatureGroupName=feature_group_name)
    print(f"Feature group '{feature_group_name}' already exists.")
except sagemaker_client.exceptions.ResourceNotFound:
    print(f"Creating Feature Group: {feature_group_name}...")
    response = sagemaker_client.create_feature_group(
        FeatureGroupName=feature_group_name,
        RecordIdentifierFeatureName=record_id_name,
        EventTimeFeatureName=event_time_name,
        FeatureDefinitions=feature_definitions,
        OfflineStoreConfig={
            "S3StorageConfig": {"S3Uri": s3_uri},
            "DisableGlueTableCreation": False
        },
        RoleArn=config["role_arn"]
    )
    print(f"Feature Group ARN: {response['FeatureGroupArn']}")

print("Waiting for Feature Group to become 'Created'...")
while True:
    status = sagemaker_client.describe_feature_group(FeatureGroupName=feature_group_name)["FeatureGroupStatus"]
    print(f"Current Status: {status}")
    if status == "Created":
        print(f"✓ Feature Group '{feature_group_name}' is ready.")
        break
    elif status == "CreateFailed":
        raise RuntimeError("Feature Group creation failed.")
    time.sleep(5)
