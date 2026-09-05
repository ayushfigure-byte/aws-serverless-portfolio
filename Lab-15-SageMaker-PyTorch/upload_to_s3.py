import boto3

sts = boto3.client('sts')
account_id = sts.get_caller_identity()['Account']
bucket_name = f"noaa-sagemaker-model-registry-{account_id}"
region = "us-east-1"

s3 = boto3.client('s3', region_name=region)

# Create the bucket (handles existing bucket gracefully)
try:
    if region == "us-east-1":
        s3.create_bucket(Bucket=bucket_name)
    else:
        s3.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration={'LocationConstraint': region}
        )
    print(f"Bucket verified/created: {bucket_name}")
except s3.exceptions.BucketAlreadyOwnedByYou:
    print(f"Bucket already exists and owned by you: {bucket_name}")

# Upload training channel
print("Uploading training channel...")
s3.upload_file("data/X_train.npy", bucket_name, "data/train/X_train.npy")
s3.upload_file("data/y_train.npy", bucket_name, "data/train/y_train.npy")

# Upload validation channel
print("Uploading validation channel...")
s3.upload_file("data/X_val.npy", bucket_name, "data/val/X_val.npy")
s3.upload_file("data/y_val.npy", bucket_name, "data/val/y_val.npy")

print("\nAll files successfully synced to S3.")
print(f"Train Channel URI: s3://{bucket_name}/data/train/")
print(f"Val Channel URI:   s3://{bucket_name}/data/val/")
