import json
import boto3
import os

bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')
sns_client = boto3.client('sns', region_name='us-east-1')

ACCOUNT_ID = boto3.client('sts').get_caller_identity()['Account']
SNS_TOPIC_ARN = f"arn:aws:sns:us-east-1:{ACCOUNT_ID}:NOAAWeatherAlerts"

def unmarshall_dynamodb_image(image):
    parsed = {}
    for key, value in image.items():
        if 'S' in value:
            parsed[key] = value['S']
        elif 'N' in value:
            parsed[key] = float(value['N'])
        elif 'BOOL' in value:
            parsed[key] = value['BOOL']
    return parsed

def generate_weather_advisory(anomaly_data):
    station = anomaly_data.get('station_id', 'Unknown')
    date = anomaly_data.get('record_date', 'Unknown')
    avg_temp = anomaly_data.get('avg_temp_f', 'N/A')
    max_temp = anomaly_data.get('max_temp_f', 'N/A')
    min_temp = anomaly_data.get('min_temp_f', 'N/A')
    z_score = anomaly_data.get('z_score', 'N/A')
    event_type = anomaly_data.get('anomaly_type', 'Extreme Outlier')

    prompt = f"""
    You are an automated meteorological risk advisor for NOAA.
    A severe statistical weather anomaly was detected:
    - Station ID: {station}
    - Date: {date}
    - Anomaly Event: {event_type}
    - Standard Deviation (Z-Score): {z_score}
    - Daily Average Temp: {avg_temp}°F
    - Temperature Range: Low {min_temp}°F / High {max_temp}°F

    Provide a concise risk summary covering:
    1. Meteorological significance of this {z_score} sigma event.
    2. Primary infrastructure risks (Energy Grid, Aviation, Public Health).
    3. Recommended immediate operational posture.

    Keep response under 150 words and format as clean bullet points.
    """

    messages = [{"role": "user", "content": [{"text": prompt}]}]

    response = bedrock_runtime.converse(
        modelId="amazon.nova-micro-v1:0",
        messages=messages,
        inferenceConfig={"maxTokens": 300, "temperature": 0.2, "topP": 0.9}
    )
    
    return response['output']['message']['content'][0]['text']

def lambda_handler(event, context):
    for record in event.get('Records', []):
        if record.get('eventName') == 'INSERT':
            new_image = record['dynamodb']['NewImage']
            anomaly = unmarshall_dynamodb_image(new_image)
            
            advisory_text = generate_weather_advisory(anomaly)
            
            subject = f"CRITICAL WEATHER ALERT: {anomaly.get('anomaly_type')} (Station {anomaly.get('station_id')})"
            message = (
                f"NOAA SEVERE ANOMALY ADVISORY\n"
                f"==============================\n"
                f"Date: {anomaly.get('record_date')}\n"
                f"Z-Score: {anomaly.get('z_score')} σ\n"
                f"Recorded Range: {anomaly.get('min_temp_f')}°F - {anomaly.get('max_temp_f')}°F\n\n"
                f"AI Risk Assessment:\n"
                f"{advisory_text}\n"
            )
            
            sns_client.publish(
                TopicArn=SNS_TOPIC_ARN,
                Subject=subject[:100],
                Message=message
            )

    return {'statusCode': 200, 'body': 'Stream processing completed successfully.'}
