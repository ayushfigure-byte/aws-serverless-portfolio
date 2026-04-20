import json
import boto3

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('T3-Training-History')

def lambda_handler(event, context):
    for record in event['Records']:
        # Parse incoming SQS JSON body
        data = json.loads(record['body'])
        
        # Structure item for the Tactical Vault (DynamoDB)
        item = {
            'AthleteID': data.get('athlete', 'Unknown'),
            'TrainingTimestamp': data.get('timestamp', '0000-00-00T00:00:00Z'),
            'Activity': data.get('activity', 'N/A'),
            'Status': data.get('status', 'Processed')
        }
        
        # Save to table
        table.put_item(Item=item)
        print(f"Successfully vaulted training data for: {item['AthleteID']}")
        
    return {
        'statusCode': 200,
        'body': json.dumps('Data Vaulted Successfully')
    }
