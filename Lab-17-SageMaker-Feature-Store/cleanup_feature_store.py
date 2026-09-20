import boto3
import json
import time

with open("feature_store_config.json") as f:
    config = json.load(f)

region = config["region"]
bucket_name = config["offline_store_bucket"]
fg_name = config["feature_group_name"]

sm = boto3.client("sagemaker", region_name=region)
s3_resource = boto3.resource("s3", region_name=region)
glue = boto3.client("glue", region_name=region)

# 1. Delete Feature Group
print(f"Deleting SageMaker Feature Group: {fg_name}...")
try:
    sm.delete_feature_group(FeatureGroupName=fg_name)
    print("✓ Feature Group deletion initiated.")
except sm.exceptions.ResourceNotFound:
    print("Feature Group already removed.")
except Exception as e:
    print(f"Error deleting Feature Group: {e}")

# 2. Check and clean Glue Table if lingering
try:
    desc = sm.describe_feature_group(FeatureGroupName=fg_name)
    glue_table = desc["OfflineStoreConfig"]["DataCatalogConfig"]["TableName"]
    glue.delete_table(DatabaseName="sagemaker_featurestore", Name=glue_table)
    print(f"✓ Dropped Glue table: {glue_table}")
except Exception:
    # Feature group deletion or previous drop already removed it
    pass

# 3. Empty and delete S3 Bucket
print(f"\nEmptying and removing S3 offline store bucket: {bucket_name}...")
bucket = s3_resource.Bucket(bucket_name)
try:
    bucket.objects.all().delete()
    bucket.object_versions.all().delete()
    bucket.delete()
    print(f"✓ Bucket {bucket_name} and all objects permanently removed.")
except Exception as e:
    print(f"S3 cleanup status: {e}")

print("\nTeardown complete.")
