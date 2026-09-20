import boto3
import json
import time

with open("feature_store_config.json") as f:
    config = json.load(f)

region = config["region"]
bucket = config["offline_store_bucket"]
fg_name = config["feature_group_name"]

sm = boto3.client("sagemaker", region_name=region)
athena = boto3.client("athena", region_name=region)

# 1. Resolve Glue Table Name
desc = sm.describe_feature_group(FeatureGroupName=fg_name)
glue_table = desc["OfflineStoreConfig"]["DataCatalogConfig"]["TableName"]
database = "sagemaker_featurestore"
output_location = f"s3://{bucket}/athena-results/"

# 2. Window Query for Snapshot Deduplication
sql = f"""
WITH ranked_features AS (
    SELECT 
        customer_id,
        churn,
        total_day_minutes,
        customer_service_calls,
        event_time,
        write_time,
        is_deleted,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id 
            ORDER BY event_time DESC, write_time DESC
        ) AS row_num
    FROM "{database}"."{glue_table}"
)
SELECT 
    customer_id,
    churn,
    total_day_minutes,
    customer_service_calls,
    event_time,
    write_time
FROM ranked_features
WHERE row_num = 1 AND is_deleted = false
ORDER BY customer_id ASC;
"""

print("Executing snapshot deduplication query via Athena...")
query_exec = athena.start_query_execution(
    QueryString=sql,
    QueryExecutionContext={"Database": database},
    ResultConfiguration={"OutputLocation": output_location}
)
query_id = query_exec["QueryExecutionId"]

while True:
    res = athena.get_query_execution(QueryExecutionId=query_id)
    state = res["QueryExecution"]["Status"]["State"]
    if state in ["SUCCEEDED", "FAILED", "CANCELLED"]:
        break
    time.sleep(1)

if state == "FAILED":
    print("Query failed:", res["QueryExecution"]["Status"]["StateChangeReason"])
    exit(1)

# 3. Display Deduplicated Snapshot
results = athena.get_query_results(QueryExecutionId=query_id)
rows = results["ResultSet"]["Rows"]

headers = [col["VarCharValue"] for col in rows[0]["Data"]]
print("\n" + "=" * 90)
print(f"{headers[0]:<15} {headers[1]:<8} {headers[2]:<19} {headers[3]:<15} {headers[4]:<15} {headers[5]}")
print("=" * 90)

for row in rows[1:]:
    data = [col.get("VarCharValue", "") for col in row["Data"]]
    print(f"{data[0]:<15} {data[1]:<8} {data[2]:<19} {data[3]:<15} {data[4]:<15} {data[5]}")
print("=" * 90)
print(f"\nTotal unique customers returned: {len(rows) - 1}")
