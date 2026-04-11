import json
import boto3
import uuid

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('SupportTickets')

def lambda_handler(event, context):
    try:
        # Parse the JSON from the frontend web form
        body = json.loads(event['body'])
        ticket_id = str(uuid.uuid4())
        
        # Save to database
        table.put_item(
            Item={
                'ticket_id': ticket_id,
                'customer_name': body['customer_name'],
                'issue': body['issue'],
                'priority': body.get('priority', 'Normal')
            }
        )
        
        # Return success WITH CORS Security Headers for the API Gateway Proxy
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'OPTIONS,POST'
            },
            'body': json.dumps({'message': 'Ticket created successfully!', 'ticket_id': ticket_id})
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {'statusCode': 500, 'body': json.dumps({'error': "Internal Server Error"})}
