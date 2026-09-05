import numpy as np
import os

np.random.seed(42)
N_DAYS = 5000
LOOKBACK = 7

# 1. Simulate 5,000 days of meteorological records with seasonal variation
time_steps = np.arange(N_DAYS)
seasonal_baseline = 70 + 20 * np.sin(2 * np.pi * time_steps / 365.25)
noise = np.random.normal(0, 3, N_DAYS)

t_max = seasonal_baseline + noise + np.random.uniform(2, 8, N_DAYS)
t_min = seasonal_baseline + noise - np.random.uniform(2, 8, N_DAYS)
t_avg = (t_max + t_min) / 2.0
pressure = 1013.25 - (t_avg - 70) * 0.3 + np.random.normal(0, 1.5, N_DAYS)
humidity = np.clip(60 - (t_avg - 70) * 0.8 + np.random.normal(0, 5, N_DAYS), 10, 100)

raw_features = np.stack([t_avg, t_max, t_min, pressure, humidity], axis=1)

# 2. Normalize features using Z-score ((value - mean) / std)
mean = raw_features.mean(axis=0)
std = raw_features.std(axis=0)
norm_features = (raw_features - mean) / std

# 3. Create sliding lookback windows
X, y = [], []
for i in range(len(norm_features) - LOOKBACK):
    X.append(norm_features[i : i + LOOKBACK])
    y.append(t_max[i + LOOKBACK])

X = np.array(X, dtype=np.float32)
y = np.array(y, dtype=np.float32).reshape(-1, 1)

# 4. Split chronologically: 80% training, 20% validation
split = int(0.8 * len(X))
X_train, y_train = X[:split], y[:split]
X_val, y_val = X[split:], y[split:]

np.save("data/X_train.npy", X_train)
np.save("data/y_train.npy", y_train)
np.save("data/X_val.npy", X_val)
np.save("data/y_val.npy", y_val)

print("=== DATA SUMMARY ===")
print(f"Total historical days: {N_DAYS}")
print(f"Training windows (X_train):   {X_train.shape}  -> 3,994 samples of (7 days × 5 features)")
print(f"Training targets (y_train):   {y_train.shape}  -> 3,994 actual next-day temperatures")
print(f"Validation windows (X_val):   {X_val.shape}   -> 999 samples")
print(f"Validation targets (y_val):   {y_val.shape}   -> 999 actual next-day temperatures")
print("\nFirst training sample target (Day 8 T_max):", round(float(y_train[0][0]), 2), "°F")
