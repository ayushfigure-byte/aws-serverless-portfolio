import boto3
import tarfile
import shutil
import os
import time

sts = boto3.client('sts')
account_id = sts.get_caller_identity()['Account']
region = "us-east-1"
bucket_name = f"noaa-sagemaker-model-registry-{account_id}"

s3 = boto3.client('s3', region_name=region)
sm = boto3.client('sagemaker', region_name=region)

# 1. Locate the latest completed training job
print("Locating latest completed training job...")
jobs = sm.list_training_jobs(
    NameContains="noaa-pytorch-lstm",
    StatusEquals="Completed",
    SortBy="CreationTime",
    SortOrder="Descending"
)
latest_job_name = jobs['TrainingJobSummaries'][0]['TrainingJobName']
job_desc = sm.describe_training_job(TrainingJobName=latest_job_name)
source_model_s3 = job_desc['ModelArtifacts']['S3ModelArtifacts']
print(f"Found trained model: {source_model_s3}")

# 2. Download and unpack trained weights
os.makedirs("deploy_staging", exist_ok=True)
s3_key = source_model_s3.replace(f"s3://{bucket_name}/", "")
s3.download_file(bucket_name, s3_key, "deploy_staging/source_model.tar.gz")

with tarfile.open("deploy_staging/source_model.tar.gz", "r:gz") as tar:
    tar.extractall("deploy_staging")

# 3. Add code/ directory (inference.py + model.py)
staging_code_dir = "deploy_staging/code"
os.makedirs(staging_code_dir, exist_ok=True)
shutil.copy("code/model.py", os.path.join(staging_code_dir, "model.py"))
shutil.copy("code/inference.py", os.path.join(staging_code_dir, "inference.py"))

# 4. Repackage into a serving model.tar.gz
serving_tar = "serving_model.tar.gz"
with tarfile.open(serving_tar, "w:gz") as tar:
    tar.add("deploy_staging/model.pth", arcname="model.pth")
    tar.add(staging_code_dir, arcname="code")

timestamp = int(time.time())
s3_serving_key = f"models/lstm-{timestamp}/model.tar.gz"
s3.upload_file(serving_tar, bucket_name, s3_serving_key)
serving_model_uri = f"s3://{bucket_name}/{s3_serving_key}"
print(f"Repackaged serving artifact uploaded to: {serving_model_uri}")

# Cleanup staging files
shutil.rmtree("deploy_staging")
os.remove(serving_tar)

# 5. Create SageMaker Model
role_arn = f"arn:aws:iam::{account_id}:role/NOAASageMakerExecutionRole"
inference_image_uri = "763104351884.dkr.ecr.us-east-1.amazonaws.com/pytorch-inference:2.1.0-cpu-py310"
model_name = f"noaa-pytorch-lstm-model-{timestamp}"

sm.create_model(
    ModelName=model_name,
    PrimaryContainer={
        'Image': inference_image_uri,
        'ModelDataUrl': serving_model_uri,
        'Environment': {
            'SAGEMAKER_PROGRAM': 'inference.py',
            'SAGEMAKER_REGION': region
        }
    },
    ExecutionRoleArn=role_arn
)
print(f"SageMaker Model resource created: {model_name}")

# 6. Create Endpoint Configuration
endpoint_config_name = f"noaa-pytorch-lstm-config-{timestamp}"
sm.create_endpoint_config(
    EndpointConfigName=endpoint_config_name,
    ProductionVariants=[{
        'VariantName': 'AllTraffic',
        'ModelName': model_name,
        'InitialInstanceCount': 1,
        'InstanceType': 'ml.m5.large'
    }]
)
print(f"Endpoint Config created: {endpoint_config_name}")

# 7. Create Real-Time Endpoint
endpoint_name = f"noaa-pytorch-lstm-endpoint-{timestamp}"
print(f"Provisioning real-time endpoint: {endpoint_name}...")
sm.create_endpoint(
    EndpointName=endpoint_name,
    EndpointConfigName=endpoint_config_name
)

# Save endpoint name for querying
with open("endpoint_name.txt", "w") as f:
    f.write(endpoint_name)

print("\nDeployment initiated successfully.")
print(f"Active Endpoint Name: {endpoint_name}")
