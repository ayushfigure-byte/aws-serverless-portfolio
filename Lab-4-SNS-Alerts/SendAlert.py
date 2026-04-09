import json
import boto3
import os

# Initialize the SNS client
sns = boto3.client('sns')

def lambda_handler(event, context):
    try:
        # 1. Grab the SNS Topic ARN from our environment variables
        sns_topic_arn = os.environ['SNS_TOPIC_ARN']
        
        # 2. Parse the incoming event
        body = json.loads(event.get('body', '{}'))
        alert_subject = body.get('subject', 'Automated System Alert')
        alert_message = body.get('message', 'A new critical event occurred in your serverless pipeline.')
        
        # 3. Publish the message to the SNS Topic
        response = sns.publish(
            TopicArn=sns_topic_arn,
            Subject=alert_subject[:100], # SNS subjects have a strict 100 char limit
            Message=alert_message
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': True, 
                'message': 'Alert broadcasted successfully!',
                'message_id': response['MessageId']
            })
        }
        
    except Exception as e:
        print(f"Error publishing to SNS: {str(e)}")
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}
