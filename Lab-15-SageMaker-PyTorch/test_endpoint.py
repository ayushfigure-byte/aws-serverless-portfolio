import boto3
import json
import numpy as np

# Load endpoint name
with open("endpoint_name.txt", "r") as f:
    endpoint_name = f.read().strip()

runtime = boto3.client("sagemaker-runtime", region_name="us-east-1")

# 1. Grab a real 7-day sequence from our local validation data
X_val = np.load("data/X_val.npy")
y_val = np.load("data/y_val.npy")

sample_idx = 42
sample_input = X_val[sample_idx].tolist()       # Shape: 7 days × 5 features
actual_temperature = float(y_val[sample_idx][0])

payload = json.dumps({"instances": [sample_input]})

print(f"Invoking Endpoint: {endpoint_name}")
print(f"Input Shape: 1 sequence of 7 days × 5 atmospheric features")

# 2. Call the SageMaker Real-Time REST endpoint
response = runtime.invoke_endpoint(
    EndpointName=endpoint_name,
    ContentType="application/json",
    Accept="application/json",
    Body=payload
)

# 3. Parse and display the forecast
result = json.loads(response["Body"].read().decode("utf-8"))
predicted_temp = result["predicted_t_max"][0]

print("\n" + "=" * 45)
print("       LIVE INFERENCE RESULT")
print("=" * 45)
print(f"Actual Next-Day T_max:     {actual_temperature:.2f} °F")
print(f"Model Predicted T_max:    {predicted_temp:.2f} °F")
print(f"Absolute Forecast Error:  {abs(actual_temperature - predicted_temp):.2f} °F")
print("=" * 45)
