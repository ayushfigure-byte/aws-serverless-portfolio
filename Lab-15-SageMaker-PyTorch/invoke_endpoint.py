import boto3
import json
import numpy as np

runtime_client = boto3.client('sagemaker-runtime', region_name='us-east-1')
ENDPOINT_NAME = "noaa-temperature-forecast-endpoint"

# 1. Load an unobserved 7-day sequence from the validation split
X_val = np.load("data/val/X_val.npy")
y_val = np.load("data/val/y_val.npy")

# Select a sample sliding window: shape (1, 7, 5)
sample_idx = 42
sample_sequence = X_val[sample_idx:sample_idx+1].tolist()
actual_tmax = float(y_val[sample_idx][0])

payload = json.dumps({"instances": sample_sequence})

print(f"Invoking Endpoint [{ENDPOINT_NAME}]...")
print(f"• Input Tensor Shape: (1, 7, 5) [1 batch, 7-day lookback, 5 normalized features]")
print(f"• Ground Truth Actual T_max: {actual_tmax:.2f}°F")
print("=" * 75)

response = runtime_client.invoke_endpoint(
    EndpointName=ENDPOINT_NAME,
    ContentType="application/json",
    Accept="application/json",
    Body=payload
)

result = json.loads(response['Body'].read().decode('utf-8'))

print("[REAL-TIME INFERENCE RESPONSE]:")
print("=" * 75)
print(f"• Predicted Next-Day Maximum Temperature: {result['predicted_t_max_fahrenheit']}°F")
print(f"• Absolute Forecast Error (|y - ŷ|):       {abs(actual_tmax - result['predicted_t_max_fahrenheit']):.2f}°F")
print(f"• Heat Advisory Trigger (≥ 95°F):         {result['heat_advisory_trigger']}")
print(f"• Severe Heat Warning Trigger (≥ 104°F):  {result['severe_heat_warning_trigger']}")
print(f"• Serving Runtime Engine:                 {result['model_version']}")
