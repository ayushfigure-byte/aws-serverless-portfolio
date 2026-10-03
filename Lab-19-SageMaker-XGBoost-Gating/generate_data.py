import numpy as np
import pandas as pd

np.random.seed(42)
n_samples = 5000

# Feature synthesis
current_temp = np.random.uniform(10.0, 35.0, n_samples)
humidity = np.random.uniform(20.0, 90.0, n_samples)
pressure = np.random.uniform(980.0, 1030.0, n_samples)
wind_speed = np.random.uniform(0.0, 25.0, n_samples)
hour = np.random.randint(0, 24, n_samples)

# Ground truth relation with noise: target is next hour temp
target_temp = current_temp + 0.5 * np.sin(hour / 24.0 * 2 * np.pi) - 0.05 * (humidity - 50.0) + np.random.normal(0, 0.8, n_samples)

# Column 0 MUST be target for built-in SageMaker XGBoost CSV format
df = pd.DataFrame({
    "target": target_temp,
    "current_temp": current_temp,
    "humidity": humidity,
    "pressure": pressure,
    "wind_speed": wind_speed,
    "hour": hour
})

# Split 80/20 train/validation
train_df = df.sample(frac=0.8, random_state=42)
val_df = df.drop(train_df.index)

# Write without headers or index
train_df.to_csv("train.csv", index=False, header=False)
val_df.to_csv("validation.csv", index=False, header=False)

print(f"Data generation complete.")
print(f"Train samples: {len(train_df)} | Validation samples: {len(val_df)}")
print("Sample row (target first):", train_df.iloc[0].values.tolist())
