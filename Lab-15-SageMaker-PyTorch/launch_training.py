import boto3
import tarfile
import time
import json

sts = boto3.client('sts')
account_id = sts.get_caller_identity()['Account']
region = "us-east-1"
bucket_name = f"noaa-sagemaker-model-registry-{account_id}"

s3 = boto3.client('s3', region_name=region)
sm = boto3.client('sagemaker', region_name=region)
iam = boto3.client('iam', region_name=region)

# 1. Ensure SageMaker Execution Role exists
role_name = "NOAASageMakerExecutionRole"
try:
    role_arn = iam.get_role(RoleName=role_name)['Role']['Arn']
    print(f"Using existing IAM Role: {role_arn}")
except iam.exceptions.NoSuchEntityException:
    print(f"Creating IAM Role: {role_name}...")
    assume_role_policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "sagemaker.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    }
    role = iam.create_role(
        RoleName=role_name,
        AssumeRolePolicyDocument=json.dumps(assume_role_policy)
    )
    iam.attach_role_policy(
        RoleName=role_name,
        PolicyArn="arn:aws:iam::aws:policy/AmazonSageMakerFullAccess"
    )
    role_arn = role['Role']['Arn']
    time.sleep(10)  # Wait for IAM propagation

# 2. Package and upload code (model.py + train.py) to S3
tar_filename = "sourcedir.tar.gz"
with tarfile.open(tar_filename, "w:gz") as tar:
    tar.add("code", arcname=".")

timestamp = int(time.time())
s3_source_key = f"source/train-{timestamp}/sourcedir.tar.gz"
s3.upload_file(tar_filename, bucket_name, s3_source_key)
source_s3_uri = f"s3://{bucket_name}/{s3_source_key}"
print(f"Uploaded training code archive to: {source_s3_uri}")

# 3. Define the SageMaker Training Job
job_name = f"noaa-pytorch-lstm-{timestamp}"
image_uri = "763104351884.dkr.ecr.us-east-1.amazonaws.com/pytorch-training:2.1.0-cpu-py310"

print(f"\nSubmitting SageMaker Training Job: {job_name}")
response = sm.create_training_job(
    TrainingJobName=job_name,
    AlgorithmSpecification={
        'TrainingImage': image_uri,
        'TrainingInputMode': 'File'
    },
    RoleArn=role_arn,
    InputDataConfig=[
        {
            'ChannelName': 'train',
            'DataSource': {
                'S3DataSource': {
                    'S3DataType': 'S3Prefix',
                    'S3Uri': f"s3://{bucket_name}/data/train/",
                    'S3DataDistributionType': 'FullyReplicated'
                }
            },
            'ContentType': 'application/x-npy'
        },
        {
            'ChannelName': 'val',
            'DataSource': {
                'S3DataSource': {
                    'S3DataType': 'S3Prefix',
                    'S3Uri': f"s3://{bucket_name}/data/val/",
                    'S3DataDistributionType': 'FullyReplicated'
                }
            },
            'ContentType': 'application/x-npy'
        }
    ],
    OutputDataConfig={
        'S3OutputPath': f"s3://{bucket_name}/model_output/"
    },
    ResourceConfig={
        'InstanceType': 'ml.m5.large',
        'InstanceCount': 1,
        'VolumeSizeInGB': 15
    },
    StoppingCondition={
        'MaxRuntimeInSeconds': 1800
    },
    HyperParameters={
        'sagemaker_program': 'train.py',
        'sagemaker_submit_directory': source_s3_uri,
        'sagemaker_region': region,
        'epochs': '15',
        'batch-size': '32',
        'lr': '0.001'
    }
)

print(f"Training job successfully triggered! ARN:")
print(response['TrainingJobArn'])
