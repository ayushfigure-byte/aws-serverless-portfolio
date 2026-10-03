# Lab 19: SageMaker Built-in XGBoost with Automated Threshold Gating & Model Registry

## Architecture Overview
This lab implements an automated, resilient MLOps workflow for weather forecasting using SageMaker built-in XGBoost, automated Boto3 metric gating, and the SageMaker Model Registry.

```
[ Synthetic Weather CSVs ]
            │
            ▼
[ S3 Input Channels: /train & /validation ]
            │
            ▼
[ SageMaker Managed XGBoost 1.7-1 Container (ECR) ]
            │ (Hyperparameters: reg:squarederror, rmse)
            ▼
[ Native Metric Extraction: describe_training_job() ]
            │
            ├── validation:rmse <= 1.0 ──► [ Model Registry: WeatherForecastingModels/1 ]
            │                                             │
            │                                             ▼
            │                                  [ Approved Audit Status ]
            │                                             │
            │                                             ▼
            │                                   [ Validated Model Entity ]
            │
            └── validation:rmse > 1.0  ──► [ Registration Halted ]
```

## Key Deliverables
- `generate_data.py`: Creates synthetic weather feature/label matrix with Column 0 target specification.
- `train_job.py`: Pure Boto3 SageMaker training job using AWS-managed XGBoost image (`683313688378.dkr.ecr.us-east-1.amazonaws.com/sagemaker-xgboost:1.7-1`).
- `gate_and_register.py`: Extracts validation RMSE (0.8356) and programmatically registers `PendingManualApproval` package version.
- Governance: Approved package version with audit rationale via AWS CLI.