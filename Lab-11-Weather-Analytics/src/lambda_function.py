import json
import time
import math
import boto3
from decimal import Decimal

athena_client = boto3.client('athena')
dynamodb = boto3.resource('dynamodb')

DATABASE = 'noaa_weather_db'
TABLE_NAME = 'NOAAWeatherAnomalies'
S3_OUTPUT_LOCATION = 's3://noaa-analytics-data-lake-as-2026/athena-results/'

def run_athena_query(query_string):
    response = athena_client.start_query_execution(
        QueryString=query_string,
        QueryExecutionContext={'Database': DATABASE},
        ResultConfiguration={'OutputLocation': S3_OUTPUT_LOCATION}
    )
    execution_id = response['QueryExecutionId']
    
    while True:
        status_resp = athena_client.get_query_execution(QueryExecutionId=execution_id)
        state = status_resp['QueryExecution']['Status']['State']
        if state == 'SUCCEEDED':
            break
        elif state in ['FAILED', 'CANCELLED']:
            reason = status_resp['QueryExecution']['Status'].get('StateChangeReason', 'Unknown error')
            raise Exception(f"Athena query {state}: {reason}")
        time.sleep(1)
        
    return athena_client.get_query_results(QueryExecutionId=execution_id)

def parse_query_results(results):
    rows = results['ResultSet']['Rows']
    if not rows:
        return []
    
    headers = [col['VarCharValue'] for col in rows[0]['Data']]
    data = []
    
    for row in rows[1:]:
        row_data = [col.get('VarCharValue', None) for col in row['Data']]
        data.append(dict(zip(headers, row_data)))
        
    return data

def lambda_handler(event, context):
    query = """
        SELECT station_id, record_date, avg_temp_f, max_temp_f, min_temp_f
        FROM noaa_weather_db.parquet_weather_data
        WHERE avg_temp_f IS NOT NULL;
    """
    
    query_results = run_athena_query(query)
    records = parse_query_results(query_results)
    
    if not records:
        return {'statusCode': 200, 'body': json.dumps({'message': 'No records retrieved.'})}
        
    temps = [float(r['avg_temp_f']) for r in records if r.get('avg_temp_f') is not None]
    n = len(temps)
    
    if n == 0:
        return {'statusCode': 400, 'body': json.dumps('No valid temperature readings.')}
        
    mean = sum(temps) / n
    variance = sum((x - mean) ** 2 for x in temps) / n
    std_dev = math.sqrt(variance)
    
    anomalies = []
    dynamo_table = dynamodb.Table(TABLE_NAME)
    
    for r in records:
        temp_val = float(r['avg_temp_f'])
        z_score = (temp_val - mean) / std_dev if std_dev > 0 else 0
        
        if abs(z_score) > 2.0:
            anomaly_type = "Extreme Heat" if z_score > 0 else "Extreme Cold"
            item = {
                'station_id': r['station_id'],
                'record_date': r['record_date'],
                'avg_temp_f': Decimal(str(round(temp_val, 2))),
                'max_temp_f': Decimal(str(round(float(r['max_temp_f']), 2))) if r.get('max_temp_f') else Decimal('0'),
                'min_temp_f': Decimal(str(round(float(r['min_temp_f']), 2))) if r.get('min_temp_f') else Decimal('0'),
                'z_score': Decimal(str(round(z_score, 2))),
                'anomaly_type': anomaly_type
            }
            dynamo_table.put_item(Item=item)
            anomalies.append(item)
            
    return {
        'statusCode': 200,
        'body': json.dumps({
            'total_records_processed': n,
            'annual_mean_temp_f': round(mean, 2),
            'std_dev_temp_f': round(std_dev, 2),
            'anomalies_flagged': len(anomalies)
        })
    }
