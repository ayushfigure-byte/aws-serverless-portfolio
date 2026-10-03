import json
import boto3

# 1. Load Persisted Training Job State
with open("job_state.json", "r") as f:
    state = json.load(f)

region = state["region"]
sm = boto3.client("sagemaker", region_name=region)

val_rmse = state["metrics"].get("validation:rmse")
print(f"Candidate Model:     {state['training_job_name']}")
print(f"Validation RMSE:     {val_rmse}")

# 2. Evaluation Gate Check
RMSE_THRESHOLD = 1.0

if val_rmse is None:
    raise ValueError("validation:rmse metric not found in training job state.")

if val_rmse > RMSE_THRESHOLD:
    print(f"\n[GATE FAILED] Validation RMSE ({val_rmse:.4f}) exceeds threshold ({RMSE_THRESHOLD}). Halting registration.")
    exit(1)

print(f"\n[GATE PASSED] Validation RMSE ({val_rmse:.4f}) <= threshold ({RMSE_THRESHOLD}). Proceeding to Model Registry.")

# 3. Ensure Model Package Group Exists
group_name = "WeatherForecastingModels"

try:
    sm.describe_model_package_group(ModelPackageGroupName=group_name)
    print(f"Found existing Model Package Group: '{group_name}'")
except sm.exceptions.ClientError:
    print(f"Creating Model Package Group: '{group_name}'")
    sm.create_model_package_group(
        ModelPackageGroupName=group_name,
        ModelPackageGroupDescription="Weather temperature regression models trained via SageMaker XGBoost"
    )

# 4. Register Candidate Model Package
print("Registering model package version...")
response = sm.create_model_package(
    ModelPackageGroupName=group_name,
    ModelPackageDescription=f"XGBoost regressor trained on {state['training_job_name']} with validation:rmse={val_rmse:.4f}",
    InferenceSpecification={
        "Containers": [
            {
                "Image": state["image_uri"],
                "ModelDataUrl": state["model_data_s3"]
            }
        ],
        "SupportedContentTypes": ["text/csv"],
        "SupportedResponseMIMETypes": ["text/csv"]
    },
    ModelApprovalStatus="PendingManualApproval"
)

package_arn = response["ModelPackageArn"]
print(f"\nSuccessfully Registered Model Package!")
print(f"Model Package ARN: {package_arn}")
