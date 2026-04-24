import json, boto3, os
sagemaker = boto3.client('sagemaker-runtime')

ENDPOINT_NAME = os.environ['ENDPOINT_NAME']

def lambda_handler(event, context):
    for record in event['Records']:
        if record['eventName'] == 'INSERT':
            new_image = record['dynamodb']['NewImage']
            hr = new_image['HR']['N']
            pace = new_image['Pace']['N']
            
            # Format as CSV for SageMaker
            payload = f"{hr},{pace}"
            response = sagemaker.invoke_endpoint(
                EndpointName=ENDPOINT_NAME,
                ContentType='text/csv',
                Body=payload
            )
            result = json.loads(response['Body'].read().decode())
            score = result['scores'][0]['score']
            
            if score > 2.0:
                print(f"TACTICAL ALERT: Anomaly Detected! Score: {score}")
