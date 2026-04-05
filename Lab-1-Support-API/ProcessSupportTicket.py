import json
import boto3
import uuid

# Initialize the DynamoDB resource
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('SupportTickets')

def lambda_handler(event, context):
    try:
        # API Gateway passes the payload as a string, so we parse it
        body = json.loads(event['body'])
        
        # Generate a unique ID for the ticket
        ticket_id = str(uuid.uuid4())
        
        # Construct the item to save
        item = {
            'ticket_id': ticket_id,
            'customer_name': body.get('name', 'Unknown'),
            'issue_description': body.get('issue', 'No description'),
            'status': 'Open'
        }
        
        # Save to DynamoDB
        table.put_item(Item=item)
        
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Ticket created successfully!', 'ticket_id': ticket_id})
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


