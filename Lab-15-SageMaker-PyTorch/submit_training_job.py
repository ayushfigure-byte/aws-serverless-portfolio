import boto3
import time
import tarfile
import os

# 1. Initialize AWS Clients
sm_client = boto3.client('sagemaker', region_name='us-east-1')
s3_client = boto3.client('s3', region_name='us-east-1')
sts_client = boto3.client('sts')

account_id = sts_client.get_caller_identity()['Account']
bucket_name = f"noaa-sagemaker-model-registry-{account_id}"
role_arn = f"arn:aws:iam::{account_id}:role/NOAASageMakerExecutionRole"
job_name = f"noaa-pytorch-lstm-{int(time.time())}"

# 2. Package Custom Training Scripts into sourcedir.tar.gz
tar_path = "sourcedir.tar.gz"
with tarfile.open(tar_path, "w:gz") as tar:
    tar.add("code", arcname=".")

s3_source_key = f"source/{job_name}/sourcedir.tar.gz"
s3_client.upload_file(tar_path, bucket_name, s3_source_key)
s3_submit_dir = f"s3://{bucket_name}/{s3_source_key}"
print(f"Uploaded training payload to {s3_submit_dir}")

# 3. Official AWS PyTorch 2.1.0 CPU Deep Learning Container (us-east-1)
training_image = "763104351884.dkr.ecr.us-east-1.amazonaws.com/pytorch-training:2.1.0-cpu-py310"

# 4. Define SageMaker create_training_job Payload
training_params = {
    "TrainingJobName": job_name,
    "RoleArn": role_arn,
    "AlgorithmSpecification": {
        "TrainingImage": training_image,
        "TrainingInputMode": "File"
    },
    "ResourceConfig": {
        "InstanceType": "ml.m5.large",
        "InstanceCount": 1,
        "VolumeSizeInGB": 30
    },
    "StoppingCondition": {
        "MaxRuntimeInSeconds": 3600
    },
    "OutputDataConfig": {
        "S3OutputPath": f"s3://{bucket_name}/model_output/"
    },
    "HyperParameters": {
        "epochs": "25",
        "batch-size": "64",
        "lr": "0.005",
        "hidden-dim": "64",
        "num-layers": "2",
        "dropout": "0.2",
        "sagemaker_program": "train.py",
        "sagemaker_submit_directory": s3_submit_dir
    },
    "InputDataConfig": [
        {
            "ChannelName": "train",
            "DataSource": {
                "S3DataSource": {
                    "S3DataType": "S3Prefix",
                    "S3Uri": f"s3://{bucket_name}/data/train/",
                    "S3DataDistributionType": "FullyReplicated"
                }
            },
            "InputMode": "File"
        },
        {
            "ChannelName": "val",
            "DataSource": {
                "S3DataSource": {
                    "S3DataType": "S3Prefix",
                    "S3Uri": f"s3://{bucket_name}/data/val/",
                    "S3DataDistributionType": "FullyReplicated"
                }
            },
            "InputMode": "File"
        }
    ]
}

# 5. Launch Training Job
print(f"Launching SageMaker Training Job: {job_name} ...")
response = sm_client.create_training_job(**training_params)
print(f"Job ARN: {response['TrainingJobArn']}")

# 6. Poll Status Until Completion
print("Monitoring job progression (polling every 20s)...")
while True:
    desc = sm_client.describe_training_job(TrainingJobName=job_name)
    status = desc['TrainingJobStatus']
    secondary = desc.get('SecondaryStatus', 'N/A')
    print(f"• Status: {status} | Step: {secondary}")

    if status in ['Completed', 'Failed', 'Stopped']:
        if status == 'Failed':
            print(f"\nTraining Failed Reason: {desc.get('FailureReason')}")
        else:
            model_artifact = desc['ModelArtifacts']['S3ModelArtifacts']
            print(f"\nTraining Successful!")
            print(f"• S3 Model Artifact: {model_artifact}")
        break
    time.sleep(20)
