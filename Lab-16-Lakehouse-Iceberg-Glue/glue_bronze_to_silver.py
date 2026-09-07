"""
glue_bronze_to_silver.py
PySpark ETL executed on AWS Glue 4.0.
Reads Bronze JSON telemetry, deduplicates records, creates an Apache Iceberg table
with hidden day partitioning, and executes an ACID MERGE INTO upsert.
"""

import sys
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql.functions import col, to_timestamp, row_number
from pyspark.sql.window import Window

# Parse job arguments passed by runner
args = getResolvedOptions(sys.argv, ["JOB_NAME", "BUCKET_NAME", "GLUE_DB"])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args["JOB_NAME"], args)

bucket = args["BUCKET_NAME"]
glue_db = args["GLUE_DB"]
bronze_input = f"s3://{bucket}/bronze/weather_telemetry/*.json"
target_table = f"glue_catalog.{glue_db}.silver_weather_readings"

print(f"Reading Bronze raw telemetry from {bronze_input} ...")
df_raw = spark.read.json(bronze_input)

# Deduplicate raw batch by event_id, keeping the latest ingest_timestamp
window_spec = Window.partitionBy("event_id").orderBy(col("ingest_timestamp").desc())
df_deduped = (
    df_raw.withColumn("row_num", row_number().over(window_spec))
    .filter(col("row_num") == 1)
    .drop("row_num")
)

# Standardize data types
df_cleaned = (
    df_deduped
    .withColumn("timestamp", to_timestamp(col("timestamp")))
    .withColumn("ingest_timestamp", to_timestamp(col("ingest_timestamp")))
    .withColumn("temperature_c", col("temperature_c").cast("double"))
    .withColumn("relative_humidity_pct", col("relative_humidity_pct").cast("double"))
    .withColumn("surface_pressure_hpa", col("surface_pressure_hpa").cast("double"))
    .withColumn("wind_speed_mps", col("wind_speed_mps").cast("double"))
    .withColumn("precipitation_mm", col("precipitation_mm").cast("double"))
    .withColumn("latitude", col("latitude").cast("double"))
    .withColumn("longitude", col("longitude").cast("double"))
    .withColumn("elevation_m", col("elevation_m").cast("double"))
)

# Register temporary view to run Spark SQL MERGE
df_cleaned.createOrReplaceTempView("bronze_updates")

# 1. Create Iceberg table if this is the initial run
# Note: uses hidden partitioning 'days(timestamp)' without creating physical folder trees
print(f"Ensuring Iceberg table {target_table} exists ...")
spark.sql(f"""
CREATE TABLE IF NOT EXISTS {target_table} (
    event_id STRING,
    station_id STRING,
    latitude DOUBLE,
    longitude DOUBLE,
    elevation_m DOUBLE,
    timestamp TIMESTAMP,
    temperature_c DOUBLE,
    relative_humidity_pct DOUBLE,
    surface_pressure_hpa DOUBLE,
    wind_speed_mps DOUBLE,
    precipitation_mm DOUBLE,
    ingest_timestamp TIMESTAMP
)
USING iceberg
PARTITIONED BY (days(timestamp))
TBLPROPERTIES (
    'format-version' = '2',
    'write.upsert.enabled' = 'true'
)
""")

# 2. Execute ACID MERGE INTO (upserts matching event_id, inserts new records)
print(f"Executing ACID MERGE INTO {target_table} ...")
spark.sql(f"""
MERGE INTO {target_table} AS target
USING bronze_updates AS source
ON target.event_id = source.event_id
WHEN MATCHED THEN
    UPDATE SET *
WHEN NOT MATCHED THEN
    INSERT *
""")

print("Iceberg Silver ETL complete.")
job.commit()