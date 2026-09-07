"""
ingest_bronze.py
Generates raw streaming NOAA weather sensor readings containing duplicates
and late arrivals, and uploads them to the Bronze lakehouse tier in S3.
"""

import json
import random
import uuid
from datetime import datetime, timedelta
import boto3

STATIONS = [
    {"id": "STATION_BWI", "lat": 39.1754, "lon": -76.6683, "elev": 43.6},
    {"id": "STATION_DCA", "lat": 38.8512, "lon": -77.0402, "elev": 4.6},
    {"id": "STATION_IAD", "lat": 38.9531, "lon": -77.4565, "elev": 95.1},
    {"id": "STATION_RIC", "lat": 37.5052, "lon": -77.3197, "elev": 50.9},
]

def load_config():
    with open("lakehouse_config.json", "r") as f:
        return json.load(f)

def generate_telemetry_batch(record_count=300):
    records = []
    base_time = datetime.utcnow()

    for _ in range(record_count):
        station = random.choice(STATIONS)
        
        # 10% chance of late-arriving data (2 to 4 days behind current time)
        is_late = random.random() < 0.10
        offset_minutes = random.randint(2880, 5760) if is_late else random.randint(0, 180)
        reading_time = base_time - timedelta(minutes=offset_minutes)

        record = {
            "event_id": str(uuid.uuid4()),
            "station_id": station["id"],
            "latitude": station["lat"],
            "longitude": station["lon"],
            "elevation_m": station["elev"],
            "timestamp": reading_time.isoformat() + "Z",
            "temperature_c": round(random.uniform(5.0, 32.0), 2),
            "relative_humidity_pct": round(random.uniform(20.0, 95.0), 1),
            "surface_pressure_hpa": round(random.uniform(990.0, 1030.0), 1),
            "wind_speed_mps": round(random.uniform(0.5, 18.0), 2),
            "precipitation_mm": round(max(0.0, random.gauss(0.5, 2.0)), 2),
            "ingest_timestamp": base_time.isoformat() + "Z"
        }
        records.append(record)

    # Intentionally inject 15 identical duplicate records
    duplicates = [records[i] for i in range(15)]
    records.extend(duplicates)
    random.shuffle(records)

    return records

def upload_batch_to_bronze():
    config = load_config()
    bucket = config["bucket_name"]
    s3 = boto3.client("s3", region_name=config["region"])

    records = generate_telemetry_batch(record_count=300)
    
    # Format as newline-delimited JSON (NDJSON) standard for big data batch files
    ndjson_data = "\n".join([json.dumps(r) for r in records])
    batch_key = "bronze/weather_telemetry/batch_01.json"

    print(f"Uploading {len(records)} raw records (including duplicates) to s3://{bucket}/{batch_key} ...")
    s3.put_object(
        Bucket=bucket,
        Key=batch_key,
        Body=ndjson_data.encode("utf-8"),
        ContentType="application/x-ndjson"
    )
    print("Bronze stage complete.")

if __name__ == "__main__":
    upload_batch_to_bronze()