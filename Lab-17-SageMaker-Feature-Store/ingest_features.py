import boto3
import json
import time
import random

with open("feature_store_config.json") as f:
    config = json.load(f)

featurestore_runtime = boto3.client(
    "sagemaker-featurestore-runtime", 
    region_name=config["region"]
)

feature_group_name = config["feature_group_name"]
current_epoch = time.time()

# 20 synthetic customer records with staggered event timestamps
print(f"Ingesting records into '{feature_group_name}'...")

sample_customers = [
    {"id": f"CUST-{1000 + i}", "churn": 1 if i % 4 == 0 else 0}
    for i in range(20)
]

for cust in sample_customers:
    # Stagger timestamps across the past 30 days to test time-travel queries later
    days_ago = random.randint(0, 30)
    event_time = current_epoch - (days_ago * 86400)

    record = [
        {"FeatureName": "customer_id", "ValueAsString": cust["id"]},
        {"FeatureName": "event_time", "ValueAsString": f"{event_time:.4f}"},
        {"FeatureName": "account_length", "ValueAsString": str(random.randint(1, 200))},
        {"FeatureName": "intl_plan", "ValueAsString": str(random.choice([0, 1]))},
        {"FeatureName": "voice_mail_plan", "ValueAsString": str(random.choice([0, 1]))},
        {"FeatureName": "total_day_minutes", "ValueAsString": f"{random.uniform(50.0, 350.0):.2f}"},
        {"FeatureName": "total_day_calls", "ValueAsString": str(random.randint(40, 160))},
        {"FeatureName": "customer_service_calls", "ValueAsString": str(random.randint(0, 6))},
        {"FeatureName": "churn", "ValueAsString": str(cust["churn"])}
    ]

    featurestore_runtime.put_record(
        FeatureGroupName=feature_group_name,
        Record=record,
        TargetStores=["OfflineStore"]
    )
    print(f"✓ Ingested record: {cust['id']} (EventTime: -{days_ago} days)")

print("\nAll 20 records successfully ingested via the PutRecord API.")
