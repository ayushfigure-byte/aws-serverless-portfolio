import json
import boto3
import urllib.parse
import uuid

# Initialize AWS SDK clients
s3 = boto3.client('s3')
textract = boto3.client('textract')
dynamodb = boto3.resource('dynamodb')

# Connect to the DynamoDB table we built
table = dynamodb.Table('ParsedDocuments')

def lambda_handler(event, context):
    try:
        # 1. Get the bucket name and file name from the S3 event trigger
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
        
        # 2. Call Amazon Textract to analyze the document
        response = textract.detect_document_text(
            Document={
                'S3Object': {
                    'Bucket': bucket,
                    'Name': key
                }
            }
        )
        
        # 3. Loop through Textract's response and stitch the text lines together
        extracted_text = ""
        for item in response['Blocks']:
            if item['BlockType'] == 'LINE':
                extracted_text += item['Text'] + " "
                
        # 4. Generate a unique ID and prepare the data for DynamoDB
        document_id = str(uuid.uuid4())
        
        item = {
            'document_id': document_id,
            'filename': key,
            'extracted_text': extracted_text.strip(),
            'status': 'Processed'
        }
        
        # 5. Save to the database
        table.put_item(Item=item)
        
        print(f"Successfully processed {key} and saved as {document_id}")
        
        return {
            'statusCode': 200,
            'body': json.dumps('Document parsed and saved successfully!')
        }
        
    except Exception as e:
        print(f"Error processing document: {str(e)}")
        raise e
