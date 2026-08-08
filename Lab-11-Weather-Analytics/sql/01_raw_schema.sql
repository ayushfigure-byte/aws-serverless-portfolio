CREATE DATABASE IF NOT EXISTS noaa_weather_db;

CREATE EXTERNAL TABLE noaa_weather_db.raw_data (
  station STRING,
  record_date STRING,
  latitude STRING,
  longitude STRING,
  elevation STRING,
  name STRING,
  temp STRING,
  temp_attributes STRING,
  dewp STRING,
  dewp_attributes STRING,
  slp STRING,
  slp_attributes STRING,
  stp STRING,
  stp_attributes STRING,
  visib STRING,
  visib_attributes STRING,
  wdsp STRING,
  wdsp_attributes STRING,
  mxspd STRING,
  gust STRING,
  max STRING,
  max_attributes STRING,
  min STRING,
  min_attributes STRING,
  prcp STRING,
  prcp_attributes STRING,
  sndp STRING,
  frshtt STRING
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
WITH SERDEPROPERTIES (
  'separatorChar' = ',',
  'quoteChar' = '"'
)
LOCATION 's3://noaa-analytics-data-lake-as-2026/raw-data/'
TBLPROPERTIES ('skip.header.line.count' = '1');
