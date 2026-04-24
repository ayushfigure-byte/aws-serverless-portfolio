import json, boto3
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('T3-Training-History')

def lambda_handler(event, context):
    for record in event['Records']:
        body = json.loads(record['body'])
        table.put_item(Item={
            'AthleteID': body['athlete'],
            'Timestamp': body['timestamp'],
            'HR': body['hr'],
            'Pace': body['pace']
        })
    return {'statusCode': 200}
