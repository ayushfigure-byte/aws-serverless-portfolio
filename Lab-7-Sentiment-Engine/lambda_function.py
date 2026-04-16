import json
import boto3
import os

s3 = boto3.client('s3')
comprehend = boto3.client('comprehend')

def lambda_handler(event, context):
    # 1. Get the bucket and file name from the S3 event
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    
    # 2. Read the text file from S3
    response = s3.get_object(Bucket=bucket, Key=key)
    text = response['Body'].read().decode('utf-8')
    
    # 3. Call Amazon Comprehend for sentiment
    sentiment_data = comprehend.detect_sentiment(Text=text, LanguageCode='en')
    sentiment = sentiment_data['Sentiment']
    
    # 4. Save the result to the Output Bucket
    output_bucket = os.environ['OUTPUT_BUCKET']
    result = {
        "original_file": key,
        "sentiment": sentiment,
        "scores": sentiment_data['SentimentScore']
    }
    
    s3.put_object(
        Bucket=output_bucket,
        Key=f"result-{key}.json",
        Body=json.dumps(result)
    )
    
    return {"status": "success"}
