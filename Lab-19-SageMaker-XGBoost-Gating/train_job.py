import boto3
import json
import time

region = "us-east-1"
account_id = "605134445337"
bucket = f"sagemaker-{region}-{account_id}"
prefix = "lab-19-xgboost"

sm = boto3.client("sagemaker", region_name=region)
iam = boto3.client("iam", region_name=region)

# 1. Resolve IAM Execution Role
role_arn = iam.get_role(RoleName="SageMakerExecutionRole")["Role"]["Arn"]

# 2. Managed XGBoost 1.7-1 Container URI for us-east-1
image_uri = f"683313688378.dkr.ecr.{region}.amazonaws.com/sagemaker-xgboost:1.7-1"
job_name = f"weather-xgb-{int(time.time())}"

print(f"Submitting Training Job: {job_name}")
print(f"Container URI:           {image_uri}")
print(f"Execution Role:          {role_arn}")

# 3. Create SageMaker Training Job via Boto3
sm.create_training_job(
    TrainingJobName=job_name,
    AlgorithmSpecification={
        "TrainingImage": image_uri,
        "TrainingInputMode": "File",
    },
    RoleArn=role_arn,
    InputDataConfig=[
        {
            "ChannelName": "train",
            "DataSource": {
                "S3DataSource": {
                    "S3DataType": "S3Prefix",
                    "S3Uri": f"s3://{bucket}/{prefix}/data/train/train.csv",
                    "S3DataDistributionType": "FullyReplicated",
                }
            },
            "ContentType": "text/csv",
        },
        {
            "ChannelName": "validation",
            "DataSource": {
                "S3DataSource": {
                    "S3DataType": "S3Prefix",
                    "S3Uri": f"s3://{bucket}/{prefix}/data/validation/validation.csv",
                    "S3DataDistributionType": "FullyReplicated",
                }
            },
            "ContentType": "text/csv",
        },
    ],
    OutputDataConfig={
        "S3OutputPath": f"s3://{bucket}/{prefix}/output"
    },
    ResourceConfig={
        "InstanceType": "ml.m5.large",
        "InstanceCount": 1,
        "VolumeSizeInGB": 10,
    },
    StoppingCondition={
        "MaxRuntimeInSeconds": 3600,
    },
    HyperParameters={
        "objective": "reg:squarederror",
        "eval_metric": "rmse",
        "num_round": "50",
        "max_depth": "5",
        "eta": "0.2",
        "subsample": "0.8",
    },
)

# 4. Poll Job Status
print("Waiting for training job to complete...")
while True:
    status = sm.describe_training_job(TrainingJobName=job_name)
    state = status["TrainingJobStatus"]
    print(f"Status: {state}")
    if state in ["Completed", "Failed", "Stopped"]:
        break
    time.sleep(15)

if state != "Completed":
    failure_reason = status.get("FailureReason", "Unknown")
    raise RuntimeError(f"Training job failed: {failure_reason}")

# 5. Extract Final Evaluation Metrics
metrics = {
    m["MetricName"]: m["Value"]
    for m in status.get("FinalMetricDataList", [])
}
print(f"\nTraining Successful!")
print(f"Final Metrics: {json.dumps(metrics, indent=2)}")

# 6. Save State for Gating Step
state_data = {
    "training_job_name": job_name,
    "model_data_s3": f"s3://{bucket}/{prefix}/output/{job_name}/output/model.tar.gz",
    "image_uri": image_uri,
    "role_arn": role_arn,
    "region": region,
    "bucket": bucket,
    "metrics": metrics,
}

with open("job_state.json", "w") as f:
    json.dump(state_data, f, indent=2)

print("Job state persisted to 'job_state.json'.")
