import numpy as np
import pandas as pd
import os
import boto3

np.random.seed(42)
N_SAMPLES = 5000
LOOKBACK = 7

# 1. Generate Synthetic Multi-Variate Time Series
time_steps = np.arange(N_SAMPLES)
seasonal_cycle = 70 + 20 * np.sin(2 * np.pi * time_steps / 365.25)
noise = np.random.normal(0, 3, N_SAMPLES)
t_max = seasonal_cycle + noise + np.random.uniform(2, 8, N_SAMPLES)
t_min = seasonal_cycle + noise - np.random.uniform(2, 8, N_SAMPLES)
t_avg = (t_max + t_min) / 2.0
pressure = 1013.25 - (t_avg - 70) * 0.3 + np.random.normal(0, 1.5, N_SAMPLES)
humidity = np.clip(60 - (t_avg - 70) * 0.8 + np.random.normal(0, 5, N_SAMPLES), 10, 100)

raw_data = np.stack([t_avg, t_max, t_min, pressure, humidity], axis=1)

# 2. Compute Mean/Std for Z-Score Normalization
mean = raw_data.mean(axis=0)
std = raw_data.std(axis=0)
norm_data = (raw_data - mean) / std

# 3. Construct Sliding Lookback Windows: (Batch, Lookback, Features) -> Target (T_max at t+1)
X, y = [], []
for i in range(len(norm_data) - LOOKBACK):
    X.append(norm_data[i : i + LOOKBACK])
    # Target is unnormalized next-day T_max for direct interpretability
    y.append(t_max[i + LOOKBACK])

X = np.array(X, dtype=np.float32)
y = np.array(y, dtype=np.float32).reshape(-1, 1)

# 4. Train / Validation Split (80/20 Chronological Split)
split_idx = int(0.8 * len(X))
X_train, y_train = X[:split_idx], y[:split_idx]
X_val, y_val = X[split_idx:], y[split_idx:]

os.makedirs("data/train", exist_ok=True)
os.makedirs("data/val", exist_ok=True)

np.save("data/train/X_train.npy", X_train)
np.save("data/train/y_train.npy", y_train)
np.save("data/val/X_val.npy", X_val)
np.save("data/val/y_val.npy", y_val)
np.save("data/scaler_stats.npy", {"mean": mean, "std": std})

print(f"Dataset generated successfully:")
print(f"• Training Set: X={X_train.shape}, y={y_train.shape}")
print(f"• Validation Set: X={X_val.shape}, y={y_val.shape}")

# 5. Upload to S3
sts = boto3.client('sts')
account_id = sts.get_caller_identity()['Account']
bucket_name = f"noaa-sagemaker-model-registry-{account_id}"
s3 = boto3.client('s3', region_name='us-east-1')

try:
    s3.create_bucket(Bucket=bucket_name)
    print(f"Created S3 bucket: {bucket_name}")
except Exception:
    pass

s3.upload_file("data/train/X_train.npy", bucket_name, "data/train/X_train.npy")
s3.upload_file("data/train/y_train.npy", bucket_name, "data/train/y_train.npy")
s3.upload_file("data/val/X_val.npy", bucket_name, "data/val/X_val.npy")
s3.upload_file("data/val/y_val.npy", bucket_name, "data/val/y_val.npy")
print(f"Data successfully synced to s3://{bucket_name}/data/")
