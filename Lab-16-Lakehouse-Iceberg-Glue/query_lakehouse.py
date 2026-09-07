"""
query_lakehouse.py
Executes queries against Athena Engine v3 to inspect Iceberg table
metadata, verify deduplication, and build Gold tier aggregations.
"""

import json
import time
import boto3

def load_config():
    with open("lakehouse_config.json", "r") as f:
        return json.load(f)

def run_athena_query(client, query_str, db_name, workgroup):
    response = client.start_query_execution(
        QueryString=query_str,
        QueryExecutionContext={"Database": db_name},
        WorkGroup=workgroup
    )
    query_execution_id = response["QueryExecutionId"]

    # Poll until query completes
    while True:
        status_res = client.get_query_execution(QueryExecutionId=query_execution_id)
        state = status_res["QueryExecution"]["Status"]["State"]
        if state in ["SUCCEEDED"]:
            break
        elif state in ["FAILED", "CANCELLED"]:
            reason = status_res["QueryExecution"]["Status"].get("StateChangeReason", "Unknown")
            raise RuntimeError(f"Query failed ({state}): {reason}")
        time.sleep(1)

    # Fetch and format tabular results
    results_paginator = client.get_paginator("get_query_results")
    rows = []
    for page in results_paginator.paginate(QueryExecutionId=query_execution_id):
        for r in page["ResultSet"]["Rows"]:
            rows.append([col.get("VarCharValue", "NULL") for col in r["Data"]])
    return rows

def print_table(title, rows):
    print(f"\n=== {title} ===")
    if not rows:
        print("No results returned.")
        return
    headers = rows[0]
    data = rows[1:]
    col_widths = [max(len(str(val)) for val in col) for col in zip(*rows)]
    format_str = " | ".join([f"{{:<{w}}}" for w in col_widths])
    
    print(format_str.format(*headers))
    print("-+-".join(["-" * w for w in col_widths]))
    for row in data:
        print(format_str.format(*row))

def main():
    config = load_config()
    client = boto3.client("athena", region_name=config["region"])
    db = config["glue_db_name"]
    wg = config["workgroup_name"]

    print(f"Connecting to Athena Engine v3 | Database: {db} | Workgroup: {wg}")

    # Query 1: Deduplication Verification
    q1 = """
    SELECT 
        COUNT(*) AS total_records,
        COUNT(DISTINCT event_id) AS distinct_events,
        COUNT(DISTINCT station_id) AS active_stations
    FROM silver_weather_readings;
    """
    rows_q1 = run_athena_query(client, q1, db, wg)
    print_table("1. Deduplication Verification (Silver Layer)", rows_q1)

    # Query 2: Inspect Iceberg Snapshots Metadata Table
    q2 = """
    SELECT 
        snapshot_id,
        parent_id,
        operation,
        committed_at,
        manifest_list
    FROM "silver_weather_readings$snapshots"
    ORDER BY committed_at DESC;
    """
    rows_q2 = run_athena_query(client, q2, db, wg)
    print_table("2. Iceberg Metadata: Snapshot History ($snapshots)", rows_q2)

    # Query 3: Inspect Iceberg Hidden Partitions
    q3 = """
    SELECT 
        partition,
        record_count,
        file_count
    FROM "silver_weather_readings$partitions"
    ORDER BY record_count DESC;
    """
    rows_q3 = run_athena_query(client, q3, db, wg)
    print_table("3. Iceberg Hidden Partitions ($partitions)", rows_q3)

    # Query 4: Create Curated Gold Layer Table
    print("\nCreating Gold Tier Table (Daily Aggregations)...")
    q4_drop = "DROP TABLE IF EXISTS gold_daily_weather_metrics;"
    run_athena_query(client, q4_drop, db, wg)

    q4_create = """
    CREATE TABLE gold_daily_weather_metrics
    WITH (
        table_type = 'ICEBERG',
        format = 'PARQUET',
        location = 's3://{bucket}/gold/daily_weather_metrics/',
        is_external = false
    ) AS
    SELECT 
        station_id,
        DATE(timestamp) AS observation_date,
        COUNT(*) AS reading_count,
        ROUND(AVG(temperature_c), 2) AS avg_temp_c,
        ROUND(MIN(temperature_c), 2) AS min_temp_c,
        ROUND(MAX(temperature_c), 2) AS max_temp_c,
        ROUND(AVG(relative_humidity_pct), 1) AS avg_humidity_pct,
        ROUND(SUM(precipitation_mm), 2) AS total_precip_mm
    FROM silver_weather_readings
    GROUP BY station_id, DATE(timestamp)
    ORDER BY station_id, observation_date;
    """.format(bucket=config["bucket_name"])
    
    run_athena_query(client, q4_create, db, wg)
    print("  Gold Iceberg table 'gold_daily_weather_metrics' created successfully.")

    # Query 5: Query Gold Summary
    q5 = """
    SELECT 
        station_id, 
        observation_date, 
        reading_count, 
        avg_temp_c, 
        min_temp_c, 
        max_temp_c, 
        total_precip_mm
    FROM gold_daily_weather_metrics
    LIMIT 10;
    """
    rows_q5 = run_athena_query(client, q5, db, wg)
    print_table("4. Curated Gold Analytics Sample", rows_q5)

if __name__ == "__main__":
    main()