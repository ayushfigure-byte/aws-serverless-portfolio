CREATE TABLE noaa_weather_db.parquet_weather_data
WITH (
    format = 'PARQUET',
    external_location = 's3://noaa-analytics-data-lake-as-2026/parquet-data-final/'
) AS
SELECT 
    '72530094846' AS station_id,
    record_date,
    TRY_CAST(temp AS DOUBLE) AS avg_temp_f,
    TRY_CAST(max AS DOUBLE) AS max_temp_f,
    TRY_CAST(min AS DOUBLE) AS min_temp_f,
    TRY_CAST(prcp AS DOUBLE) AS precipitation_in
FROM noaa_weather_db.raw_data;
