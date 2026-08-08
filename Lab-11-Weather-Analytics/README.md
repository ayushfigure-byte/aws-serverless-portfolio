# Lab 11: Serverless Weather Analytics & Anomaly Detection

An end-to-end serverless data lake and statistical anomaly detection pipeline built on AWS.

## Architecture
1. **S3 Landing Zone:** Ingests raw NOAA GSOD meteorological CSV files.
2. **Amazon Athena (OpenCSVSerde):** Maps raw positional text columns.
3. **Amazon Athena (CTAS):** Transforms text CSV rows into columnar Apache Parquet files.
4. **AWS Lambda (Python 3.12):** Executes Boto3 queries, calculates population mean ($\mu$) and standard deviation ($\sigma$), and filters outliers ($|z| > 2.0$).
5. **Amazon DynamoDB:** Stores severe weather anomaly records in On-Demand capacity mode ($0 idle spend).
